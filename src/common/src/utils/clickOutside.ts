import type { DirectiveBinding, ObjectDirective } from 'vue';

interface HTMLElementWithClickOutside extends HTMLElement {
  clickOutsideEvent?: (event: MouseEvent) => void;
}

const clickOutside: ObjectDirective = {
  beforeMount(el: HTMLElementWithClickOutside, binding: DirectiveBinding) {
    el.clickOutsideEvent = (event: MouseEvent) => {
      // Verify if the click was outside the element
      if (!(el === event.target || el.contains(event.target as Node))) {
        binding.value(event);
      }
    };
    // Delay the attachment of the event listener to prevent closing 
    // the element before its shown
    setTimeout(() => {
      document.addEventListener('click', el.clickOutsideEvent!);
    }, 0);
  },
  unmounted(el: HTMLElementWithClickOutside) {
    document.removeEventListener('click', el.clickOutsideEvent!);
  }
};

export default clickOutside;
