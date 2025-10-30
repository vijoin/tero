import logging
from typing import Any, Dict, Optional, Sequence, cast, Callable

from jinja2 import Environment
from jinja2.nodes import Output, TemplateData, If, For, Getattr, Node, Name, Template, Call, Tuple


logger = logging.getLogger(__name__)


class JinjaTemplateParser:
    
    def __init__(self, env: Environment):
        self._env = env
        self._rendered_position = 0
        
    def parse(self, rendered: str, template_body: str) -> Dict[str, Any]:
        ast = self._env.parse(template_body)
        return self._parse_from_node(rendered + "\n", ast, None)

    def _parse_from_node(self, rendered: str, node: Node, next: Optional[Node]) -> Dict[str, Any]:
        ret = {}
        if isinstance(node, Template):
            self._parse_children(node.body, ret, lambda child, next: self._parse_from_node(rendered, child, next))
        elif isinstance(node, Output):
            self._parse_children(node.nodes, ret, lambda child, next: self._parse_from_node(rendered, child, next))
        elif isinstance(node, TemplateData):
            self._update_rendered_position(rendered, node.data)
        elif isinstance(node, Name):
            ret[node.name] = self._solve_expression(rendered, node, next)
        elif isinstance(node, Getattr):
            self._merge_dicts(ret, self._solve_attr_dict(node.node, {node.attr: self._solve_expression(rendered, node, next)}))
        elif isinstance(node, If):
            self._merge_dicts(ret, self._parse_if_node(rendered, node))
        elif isinstance(node, For):
            self._merge_dicts(ret, self._parse_for_node(rendered, node)) 
        return ret

    def _parse_children(self, children: Sequence[Node], ret: Dict[str, Any], child_parser: Callable[[Node, Optional[Node]], Dict[str, Any]]):
        last = None
        for child in children:
            if last:
                self._merge_dicts(ret, child_parser(last, child))
            last = child
        if last:
            self._merge_dicts(ret, child_parser(last, None))

    def _update_rendered_position(self, rendered: str, data: str):
        if not rendered[self._rendered_position:].startswith(data):
            raise ValueError(f"Template data '{data}' not found at position {self._rendered_position}. Found '{rendered[self._rendered_position:min(self._rendered_position + 100, len(rendered))].strip()}'")
        self._rendered_position += len(data)

    def _solve_expression(self, rendered: str, node: Node, next: Optional[Node]) -> Any:
        if not isinstance(next, TemplateData):
            raise ValueError(f"Expected TemplateData as next node of {node}, got {next}")
        start_pos = self._rendered_position
        self._rendered_position = rendered.find(next.data, start_pos)
        return rendered[start_pos:self._rendered_position]

    def _solve_attr_dict(self, node: Node, val: Any) -> Dict[str, Any]:
        if isinstance(node, Name):
            return {node.name: val}
        elif isinstance(node, Getattr):
            return self._solve_attr_dict(node.node, {node.attr: val})
        elif isinstance(node, Call):
            if not isinstance(node.node, Getattr) or node.node.attr != "items":
                raise ValueError(f"Unknown call: {node}")
            attr = cast(Getattr, node.node)
            return self._solve_attr_dict(attr.node, val)
        else:
            raise ValueError(f"Unknown node: {node}")

    def _merge_dicts(self, base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value
        return base

    def _parse_if_node(self, rendered: str, node: If) -> Dict[str, Any]:
        ret = {}
        if not self._starts_with_child_data(rendered, node.body, node):
            return ret
        self._parse_children(node.body, ret, lambda child, next: self._parse_from_node(rendered, child, next))
        return ret

    def _starts_with_child_data(self, rendered: str, children: Sequence[Node], parent: Node) -> bool:
        return rendered[self._rendered_position:].startswith(self._find_child_data(children, parent))

    def _find_child_data(self, children: Sequence[Node], parent: Node) -> str:
        output = children[0]
        if not isinstance(output, Output):
            raise ValueError(f"Invalid template with if without immediate output: '{parent}'")
        data = output.nodes[0]
        if not isinstance(data, TemplateData):
            raise ValueError(f"Invalid template with if without immediate data: '{parent}'")
        return data.data

    def _parse_for_node(self, rendered: str, node: For) -> Dict[str, Any]:
        if isinstance(node.target, Tuple):
            if len(node.target.items) != 2:
                raise ValueError(f"Expected 2 items in tuple for for loop, got {len(node.target.items)}")
            key = cast(Name, node.target.items[0]).name
            value = cast(Name, node.target.items[1]).name
            ret = {}
            while self._starts_with_child_data(rendered, node.body, node):
                self._parse_children(node.body, ret, lambda child, next: self._parse_key_val_node(rendered, key, value, node.iter, child, next))
        else:
            key = cast(Name, node.target).name
            ret_list = []
            while self._starts_with_child_data(rendered, node.body, node):
                iter_result = {}
                self._parse_children(node.body, iter_result, lambda child, next: self._parse_from_node(rendered, child, next))
                ret_list.append(iter_result[key])
            ret = self._solve_attr_dict(node.iter, ret_list)
        return ret

    def _parse_key_val_node(self, rendered: str, key: str, value: str, iter: Node, node: Node, next: Optional[Node]) -> Dict[str, Any]:
        parsed = self._parse_from_node(rendered, node, next)
        return self._solve_attr_dict(iter, {parsed[key]: parsed[value]})
