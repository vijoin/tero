declare module "emoji-js" {
  class EmojiConvertor {
    constructor();
    replace_colons(text: string): string;
  }

  export = EmojiConvertor;
}
