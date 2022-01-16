import { keymap } from "prosemirror-keymap";
import { history } from "prosemirror-history";
import { baseKeymap } from "prosemirror-commands";
import { Plugin } from "prosemirror-state";
import { dropCursor } from "prosemirror-dropcursor";
import { gapCursor } from "prosemirror-gapcursor";
import { menuBar } from "prosemirror-menu";
import { mathPlugin } from "@benrbray/prosemirror-math";
import { buildMenuItems } from "./menu";
import { buildKeymap } from "./keymap";
import { buildInputRules } from "./inputrules";
import { inputRules } from "prosemirror-inputrules";
import { liftListItem, sinkListItem } from "prosemirror-schema-list";
import { tableEditing } from "prosemirror-tables";
import {
  makeBlockMathInputRule, makeInlineMathInputRule,
  REGEX_INLINE_MATH_DOLLARS, REGEX_BLOCK_MATH_DOLLARS
} from "@benrbray/prosemirror-math";


// !! This module exports helper functions for deriving a set of basic
// menu items, input rules, or key bindings from a schema. These
// values need to know about the schema for two reasons—they need
// access to specific instances of node and mark types, and they need
// to know which of the node and mark types that they know about are
// actually present in the schema.
//
// The `exampleSetup` plugin ties these together into a plugin that
// will automatically enable this basic functionality in an editor.

// :: (Object) → [Plugin]
// A convenience plugin that bundles together a simple menu with basic
// key bindings, input rules, and styling for the example schema.
// Probably only useful for quickly setting up a passable
// editor—you'll need more control over your settings in most
// real-world situations.
//
//   options::- The following options are recognized:
//
//     schema:: Schema
//     The schema to generate key bindings and menu items for.
//
//     mapKeys:: ?Object
//     Can be used to [adjust](#example-setup.buildKeymap) the key bindings created.
//
//     menuBar:: ?bool
//     Set to false to disable the menu bar.
//
//     history:: ?bool
//     Set to false to disable the history plugin.
//
//     floatingMenu:: ?bool
//     Set to false to make the menu bar non-floating.
//
//     menuContent:: [[MenuItem]]
//     Can be used to override the menu content.
export function exampleSetup(options) {
  function insertLink(state, dispatch) {
    let title = prompt("Object Title");
    let node = options.schema.nodes.wikilinknode.create({ title });
    dispatch(state.tr.replaceSelectionWith(node, false));
    return true;
  }
  function insertLinkMark(state, dispatch) {
    let title = prompt("Object Title");
    let node = options.schema.text(title, [options.schema.marks.wikilinkmark.create({ title: title })]);
    dispatch(state.tr.replaceSelectionWith(node, false));
  }
  // create input rules (using default regex)
  let inlineMathInputRule = makeInlineMathInputRule(REGEX_INLINE_MATH_DOLLARS, options.schema.nodes.math_inline);
  let blockMathInputRule = makeBlockMathInputRule(REGEX_BLOCK_MATH_DOLLARS, options.schema.nodes.math_display);

  let plugins = [
    buildInputRules(options.schema),
    keymap(buildKeymap(options.schema, options.mapKeys)),
    keymap(baseKeymap),
    dropCursor(),
    gapCursor(),
    mathPlugin,
    keymap({
      "Shift-Tab": liftListItem(options.schema.nodes.list_item),
      "Tab": sinkListItem(options.schema.nodes.list_item),
      "Ctrl-Space": insertLink,
      "Ctrl-e": insertLinkMark,
    }),
    inputRules({ rules: [inlineMathInputRule, blockMathInputRule] }),
    tableEditing(),
  ];
  if (options.menuBar !== false) {
    plugins.push(menuBar({
      floating: options.floatingMenu !== false,
      content: options.menuContent || buildMenuItems(options.schema).fullMenu
    }));
  };
  if (options.history !== false)
    plugins.push(history());

  return plugins.concat(new Plugin({
    props: {
      attributes: { class: "ProseMirror-example-setup-style" }
    }
  }));
}
