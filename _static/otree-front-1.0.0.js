/** 
 * Utils to handle references to game state vars and manage their updates.
 * 
 * The references are just strings in form `obj.field.subfield`
 * 
 * @module utils/changes/Ref 
 */

const jspath_re = new RegExp(/^[a-zA-Z]\w+(\.\w+)*$/);

/**
 * Validates syntax of a reference 
 * 
 * @param {string} ref
 * @throws {Error}
 */
function validate(ref) {
  if (!ref || !jspath_re.exec(ref)) throw new Error(`Invalid ref: ${ref}`);
}

/**
 * Checks if references overlap 
 * 
 * Example: `Ref.includes("foo.bar", "foo.bar.baz")`
 * 
 * @param {string} parentref reference to parent object
 * @param {string} nestedref reference to nested field
 * @returns {boolean}
 */
function includes(parentref, nestedref) {
  return parentref == nestedref || nestedref.startsWith(parentref + ".");
}

/**
 * Strips common part of nested ref, making it local to parent
 *
 * Example: `Ref.strip("foo.bar", "foo.bar.baz") == "baz"`
 * 
 * @param {string} parentref reference to parent object
 * @param {string} nestedref reference to nested field
 * @returns {boolean}
 */
function strip(parentref, nestedref) {
  if (parentref == nestedref) {
    return "";
  } else if (nestedref.startsWith(parentref + ".")) {
    return nestedref.slice(parentref.length + 1);
  } else {
    throw new Error(`Incompatible refs: ${parentref} / ${nestedref}`);
  }
}

/**
 * Extract a value from object by a ref
 * 
 * Example: `Ref.extract({ foo: { bar: "Bar" } }, "foo.bar") == "Bar"`
 * 
 * @param {object} data 
 * @param {string} ref 
 * @returns {boolean}
 */
function extract(data, ref) {
  return ref.split(".").reduce((o, k) => (o && k in o ? o[k] : undefined), data);
}

/**
 * Sets a value in object by ref.
 * The original object is modified in place
 * 
 * Example: `Ref.update({foo: {bar: "Bar0" } }, "foo.bar", "Bar1") → {foo: {bar: "Bar1" } }`
 * 
 * @param {object} data 
 * @param {ref} ref 
 * @param {*} value 
 */
function update(data, ref, value) {
  function ins(obj, key) {
    return (obj[key] = {});
  }

  const path = ref.split("."),
    objpath = path.slice(0, -1),
    fld = path[path.length - 1];

  let obj = objpath.reduce((o, k) => (k in o ? o[k] : ins(o, k)), data);
  if (obj === undefined) throw new Error(`Incompatible ref ${ref}`);
  if (value === undefined) {
    delete obj[fld];
  } else {
    obj[fld] = value;
  }
}

var ref = /*#__PURE__*/Object.freeze({
  __proto__: null,
  validate: validate,
  includes: includes,
  strip: strip,
  extract: extract,
  update: update
});

/** 
 * Utils to handle changes of game state data
 * 
 * @module utils/changes
 */

/**
 * A set of references to vars and their new values.
 * 
 * The references are in form `obj.field.subfield` and correspond to a game state.  
 */
class Changes extends Map {
  /**
   * @param {object} obj plain object describing changes 
   * @param {string} [prefix] a prefix to add to all the top-level fields, as if there was an above-top object  
   */
  
  constructor(obj, prefix) {
    let entries = [...Object.entries(obj)];
    if (prefix) {
      entries = entries.map(([k, v]) => [prefix + "." + k, v]);
    } 
    super(entries);
    this.forEach((v, k) => validate(k));
  }

  /** 
   * Checks if the changeset contains referenced var 
   * 
   * Example:
   *   ```
   *   changes = new Changes({ 'obj.foo': { ... } })
   *   changes.afects("obj.foo.bar") == true // becasue the `bar` is contained in `obj.foo` 
   *   ```
   * @param {string} ref
   */
  affects(ref$1) {
    return [...this.keys()].some((key) => includes(key, ref$1));
  }

  /** 
   * Picks single value from changeset.
   * 
   * Example:  
   *   ```
   *   changes = new Changes({ 'obj.foo': { bar: "Bar" } })
   *   changes.pick("obj.foo.bar") == "Bar"
   *   ```
   */
  pick(ref$1) {
    let affecting = [...this.keys()].filter((key) => includes(key, ref$1));
    if (affecting.length == 0) return undefined;
    if (affecting.length != 1) throw new Error(`Incompatible changeset for ${ref$1}`);
    affecting = affecting[0];

    let value = this.get(affecting);

    if (affecting == ref$1) {
      return value;
    } else {
      return extract(value, strip(affecting, ref$1));
    }
  }

  /** 
   * Apply changes
   * 
   * Modify an obj by all the changes.
   * 
   * Example:
   *    ```
   *    obj = { obj: { foo: { bar: "xxx" } } } 
   *    changes = new Changes({ 'obj.foo': { bar: "Bar" } })
   *    changes.patch(obj)
   * 
   *    obj == { obj: { foo: { bar: "Bar" } } }
   *    ```
   * 
   * It works with arrays as well, when using indexes as subfields.
   * 
   */
  patch(obj) {
    this.forEach((v, k) => {
      update(obj, k, v);
    });
  }
}

var changes = /*#__PURE__*/Object.freeze({
  __proto__: null,
  Ref: ref,
  Changes: Changes
});

/** 
 * Set of simple utils to manipulate DOM
 * @module utils/dom
 */

/** 
 * Loads an image asynchronously
 * 
 * Example:
 *   ```
 *   img = await loadImage("http://example.org/image.png");
 *   ```
 *  
 * @param {string} url url or dataurl to load
 * @returns {Promise} resolving to Image object
 */
function loadImage(url) {
  const img = new Image();
  return new Promise((resolve, reject) => {
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = url;
  });
}

/** 
 * Toggles visibility by setting 'display' css property.
 * 
 * @param {HTMLElement} elem
 * @param {boolean} display
 */
function toggleDisplay(elem, display) {
  elem.style.display = display ? null : "none";
}

/** 
 * Toggles disabled state by `.disabled` property (for inputs), and also `ot-disabled` class.
 * 
 * @param {HTMLElement} elem
 * @param {boolean} disabled
 */
 function toggleDisabled(elem, disabled) {
  elem.disabled = disabled;
  elem.classList.toggle("ot-disabled", disabled);
}

/** 
 * Checks if elem is disabled 
 * @param {HTMLElement} elem
 */
function isDisabled(elem) {
  return elem.classList.contains("ot-disabled");
}

/** 
 * Sets or deletes text content 
 * @param {HTMLElement} elem
 * @param {string|null} text 
 */
function setText(elem, text) {
  // NB: using `innerText` to render line breaks
  elem.innerText = text == null ? "" : text;
}

/** 
 * Sets element classes 
 * @param {HTMLElement} elem
 * @param {string[]} classes
 */
function setClasses(elem, classes) {
  elem.classList.remove(...elem.classList);
  elem.classList.add(...classes);
}

/** 
 * Sets or deletes an attribute 
 * 
 * @param {HTMLElement} elem
 * @param {string} attr
 * @param {string|null} val
 */
function setAttr(elem, attr, val) {
  if (val == null) {
    elem.removeAttribute(attr);
  } else {
    elem.setAttribute(attr, val);
  }
}

/** 
 * Inserts single child element or empties elem.
 *  
 * @param {HTMLElement} elem
 * @param {HTMLElement|null} child
 */
function setChild(elem, child) {
  if (child == null) {
    elem.replaceChildren();
  } else {
    elem.replaceChildren(child);
  }
}

/** 
 * Checks if an elem is a text input or textarea
 *  
 * @param {HTMLElement} elem
 * @returns {boolean}
 */
function isTextInput(elem) {
  return (elem.tagName == "INPUT" && elem.type == "text") || elem.tagName == "TEXTAREA";
}

var dom = /*#__PURE__*/Object.freeze({
  __proto__: null,
  loadImage: loadImage,
  toggleDisplay: toggleDisplay,
  toggleDisabled: toggleDisabled,
  isDisabled: isDisabled,
  setText: setText,
  setClasses: setClasses,
  setAttr: setAttr,
  setChild: setChild,
  isTextInput: isTextInput
});

/** @module utils/random */

/**
 * Makes random choice from an array
 * 
 * @param {Array} choices
 */
function choice(choices) {
  return choices[Math.floor(Math.random() * choices.length)];
}

var random = /*#__PURE__*/Object.freeze({
  __proto__: null,
  choice: choice
});

/** @module utils/timers */


/**
 * Async sleeping
 * 
 * @param {number} time in ms 
 * @returns {Promise}
 */
async function sleep(time) {
    return new Promise((resolve, reject) => {
        setTimeout(() => resolve(), time);
    });
}

/**
 * Delays function call
 * 
 * @param {Function} fn 
 * @param {number} delay in ms 
 * @returns {*} timer_id 
 */
function delay(fn, delay=0) {
    return window.setTimeout(fn, delay);
}

/**
 * Cancels delayed call
 * 
 * @param {*} id timer_id 
 */
function cancel(id) {
    window.clearTimeout(id);
}

/** 
 * Timers.
 * 
 * A set of timers with names
 */
class Timers {
    constructor() {
        this.timers = new Map();
    }

    /**
     * Delays function call
     * 
     * @param {sting} name 
     * @param {Function} fn 
     * @param {number} timeout in ms
     */
    delay(name, fn, timeout=0) {
        if (this.timers.has(name)) {
            cancel(this.timers.get(name));
        }
        this.timers.set(name, delay(fn, timeout));
    }

    /**
     * Cancels delayed calls by names.
     * 
     * @param  {...string} names one or more named calls to cancel, empty to cancel all 
     */
    cancel(...names) {
        if (names.length != 0) {
            names.forEach((n) => {
                cancel(this.timers.get(n));
                this.timers.delete(n);
            });
        } else {
            this.timers.forEach((v, k) => cancel(v));
            this.timers.clear();
        }
    }
}

var timers = /*#__PURE__*/Object.freeze({
  __proto__: null,
  sleep: sleep,
  delay: delay,
  cancel: cancel,
  Timers: Timers
});

/**
 * Begins measurement
 *
 * @param {string} name
 */
function begin(name) {
  const mark_beg = `otree.${name}.beg`;
  performance.clearMarks(mark_beg);
  performance.mark(mark_beg);
}

/**
 * Ends measurement
 *
 * @param {string} name
 * @returns {number} duration in mseconds
 */
function end(name) {
  const mark_end = `otree.${name}.end`;
  performance.clearMarks(mark_end);
  performance.mark(mark_end);

  const mark_beg = `otree.${name}.beg`;
  const measure = `otree.${name}.measure`;
  performance.clearMeasures(measure);
  performance.measure(measure, mark_beg, mark_end);

  const entry = performance.getEntriesByName(measure)[0];
  return entry.duration;
}

var measurement = /*#__PURE__*/Object.freeze({
  __proto__: null,
  begin: begin,
  end: end
});

/* map of selector => class */
const registry = new Map();

/** 
 * Registers a directive class.
 * 
 * The {@link Page} sets up all registered directives on all found elements in html.
 * The elements a searched by provided selector, which is something like `[ot-something]` but actually can be anything.
 * 
 * @param {string} selector a css selector for elements
 * @param {class} cls a class derived from {@link DirectiveBase}  
 */
function registerDirective(selector, cls) {
  registry.set(selector, cls);
}

/** 
 * Base class for directives.
 * 
 * Used by all built-in directives and can be used to create custom directives.
 */
class DirectiveBase {
  /** 
   * directive name
   * 
   * like "foo" for `ot-foo`
   * 
   * should be redefined in derived classes 
   */  
  get name() {
    return "foo";
  }

  /** 
   * Returns a value from attribute `ot-name`.
   * 
   * @param {string} [name=this.name] the param to get 
   */
  param(attr) {
    if (attr === undefined) attr = this.name; 
    return this.elem.getAttribute(`ot-${attr}`)
  }

  /**
   * A directive instance is created for each matching element.
   * 
   * @param {Page} page 
   * @param {HTMLElement} elem 
   */
  constructor(page, elem) {
    this.page = page;
    this.elem = elem;
    this.handlers = new Map();
    this.init();
  }

  /** 
   * Binds an event handler.
   * 
   * Shorcut for page.on, with the handler bound to `this` directive.
   * 
   * @param {String} eventype
   * @param {Function} handler either `this.something` or a standalone function
   * @param {HTMLElement} [target=page.body] either the element itself or the page 
  */
  onEvent(eventype, handler, target) {
    this.page.onEvent(eventype, (event) => handler.bind(this)(event, event.detail), target);
  }

  /** 
   * Initializes directive.
   *  
   * Use it to parse parameters from the element, and to init all the state.
   * 
   * Default implementation takes reference from corresponding attr and puts it into `this.ref`   
   */
  init() {
    this.ref = this.param();
    validate(this.ref); 
  } 

  /**
   * Sets up event handlers
   * 
   * Default implementation sets up handlers for `reset` and `update` events, 
   * checking if `this.ref` is affected by event and calling `this.reset` or `this.update` 
   */
  setup() {
    this.onEvent('ot.reset', this.onReset);
    this.onEvent('ot.update', this.onUpdate);
  }
  
  onReset(event, vars) {
    if (vars == "*" || vars.some(topname => includes(topname, this.ref))) {
      this.reset(vars);
    }
  }

  /**
   * Called in default imlementation when `reset` event affects `this.ref`.
   * 
   * Override to do something useful.
   */
  reset() {
    // do something
    throw new Error("Method not implemented");
  }

  onUpdate(event, changes) {
    if (changes.affects(this.ref)) {
      this.update(changes);
    }
  }

  /**
   * Called in default imlementation when `update` event affects `this.ref`.
   * 
   * Override to do something useful.
   *  
   * @param {Changes} changes 
   */
  update(changes) {
    // do something
    throw new Error("Method not implemented");
  }
}

/**
 * Directive `ot-ready`
 * 
 * It is activated by any configured trigger `ot-key="keycode"`, `ot-touch`, `ot-click`, and triggers {@link Page.event:start}. 
 * 
 * @hideconstructor
 */
class otReady extends DirectiveBase {
  get name() {
    return "ready";
  }

  init() {
    this.trigger = {
      click: this.elem.hasAttribute("ot-click"),
      touch: this.elem.hasAttribute("ot-touch"),
      key: this.elem.hasAttribute("ot-key") ?  this.elem.getAttribute("ot-key"): false,
    };
    this.disabled = false;
  }

  setup() {
    if (this.trigger.key) this.onEvent("keydown", this.onKey);
    if (this.trigger.touch) this.onEvent("touchend", this.onClick, this.elem);
    if (this.trigger.click) this.onEvent("click", this.onClick, this.elem);
    this.onEvent('ot.ready', this.onStart);
  }

  onKey(event) {
    if (this.disabled) return;
    if (event.code != this.trigger.key) return;
    event.preventDefault();
    this.page.emitEvent('ot.ready'); 
  }

  onClick(event) {
    if (this.disabled) return;
    event.preventDefault();
    this.page.emitEvent('ot.ready'); 
  }

  onStart() {
    toggleDisplay(this.elem, false);
    toggleDisabled(this.elem, true);
  }
}

registerDirective("[ot-ready]", otReady);

/**
 * Directive `ot-display="phaseflag"`
 * 
 * It shows/hides an element when {@link Phase} contains matching `display` field.
 * If the phase doesn't contain the field, it is ignored (i.e. phases toggling just `inputEnabled` do not affect the display). 
 * 
 * @hideconstructor
 */
class otDisplay extends DirectiveBase {
  get name() {
    return "display";
  }

  init() {
    let param = this.param();
    const match = param.match(/^\w+(\|\w+)?$/);
    if (!match) throw new Error(`Invalid display phase: ${this.phase}`);

    this.phases = param.split('|');
  }

  setup() {
    this.onEvent('ot.phase', this.onPhase);
  }
  
  onPhase(event, phase) {
    if (!('display' in phase)) return;
    toggleDisplay(this.elem, this.phases.includes(phase.display));
  }
}

registerDirective("[ot-display]", otDisplay);

/**
 * Directive `ot-input` for native inputs: `<input>`, `<select>`, `<textarea>`.
 * 
 * It triggers {@link Page.event:response} when value of the input changes.
 * For text inputs it triggers when `Enter` pressed.
 * 
 * The input gets disabled according to {@link Phase} flag `input` 
 * 
 * @hideconstructor
 */
class otRealInput extends DirectiveBase {
  get name() {
    return "input";
  }

  init() {
  }

  setup() {
    this.onEvent("ot.reset", this.onReset);
    this.onEvent("ot.phase", this.onPhase);
    this.onEvent("change", this.onChange, this.elem);
    if (isTextInput(this.elem)) this.onEvent("keydown", this.onKey, this.elem);
  }

  onReset(event, vars) {
    this.elem.value=null;
  }

  onPhase(event, phase) {
    toggleDisabled(this.elem, !phase.inputEnabled);
  }

  onChange(event) {
    let value = this.elem.value;
    if (value === "true") value = true;
    if (value === "false") value = false;
    this.page.emitInput(this.elem.name, value);
  }

  onKey(event) {
    if (event.code == "Enter") {
      // enforce change event
      setTimeout(() =>
      this.elem.dispatchEvent(
          new Event("change", {
            view: window,
            bubbles: false,
            cancelable: true,
          })
        )
      );
    }
  }
}

registerDirective(
  "input[ot-input], select[ot-input], textarea[ot-input]",
  otRealInput
);


/**
 * Directive `ot-input` for custom inputs: any `<div>`, `<span>`, `<button>`, `<kbd>`.
 * 
 * The directive should be accompanied with method of triggering `ot-
 * 
 * It triggers {@link Page.event:response} by a configred trigger:
 * - `ot-click` to trigger on click
 * - `ot-touch` to trigger on touch
 * - `ot-key="keycode" to trigger on keypress
 * 
 * The list of available is at MDN: https://developer.mozilla.org/en-US/docs/Web/API/KeyboardEvent/code/code_values  
 * Basically, it is something like 'Enter', 'Space', 'Escape', or 'KeyQ' for "q" key.
 * 
 * The input gets disabled according to {@link Phase} flag `input` 
 * 
 * @hideconstructor
 */
class otCustomInput extends DirectiveBase {
  get name() {
    return "input";
  }

  init() {
    this.inp_name = this.elem.getAttribute('name');
    this.inp_value = this.elem.getAttribute('value');

    if (this.inp_value === undefined) {
      throw new Error("Missing value attribute for ot-input");
    }

    if (this.inp_value === "true") this.inp_value = true;
    if (this.inp_value === "false") this.inp_value = false; 

    this.trigger = {
      click: this.elem.hasAttribute("ot-click"),
      touch: this.elem.hasAttribute("ot-touch"),
      key: this.elem.hasAttribute("ot-key") ?  this.elem.getAttribute("ot-key"): false,
    };

    if (this.elem.tagName == "BUTTON") this.trigger.click = true; 
  }

  setup() {
    this.onEvent("ot.phase", this.onPhase);
    if (this.trigger.key) this.onEvent("keydown", this.onKey);
    if (this.trigger.touch) this.onEvent("touchend", this.onClick, this.elem);
    if (this.trigger.click) this.onEvent("click", this.onClick, this.elem);
  }

  onPhase(event, phase) {
    if (!('inputEnabled' in phase)) return;
    toggleDisabled(this.elem, !phase.inputEnabled);
  }

  onClick(event) {
    if (isDisabled(this.elem)) return;
    event.preventDefault();
    this.page.emitInput(this.inp_name, this.inp_value);  
  }

  onKey(event) {
    if (isDisabled(this.elem)) return;
    if (event.code != this.trigger.key) return;
    event.preventDefault();
    this.page.emitInput(this.inp_name, this.inp_value);  
  }
}

registerDirective(
  "div[ot-input], span[ot-input], button[ot-input], kbd[ot-input]",
  otCustomInput
);

/**
 * Directive `ot-class="reference"`
 * 
 * It adds a class with a value from `{@link Page.event:update}`.
 * All other existing lasses are preserved. 
 */
class otClass extends DirectiveBase {
  get name() {
    return "class";
  }

  init() {
    super.init();
    this.defaults = Array.from(this.elem.classList);
  }

  reset() {
    setClasses(this.elem, this.defaults);
  }

  update(changes) {
    let classes = this.defaults.slice();
    let val = changes.pick(this.ref);
    if (!!val) {
      classes.push(val);
    }
    setClasses(this.elem, classes);
  }
}

registerDirective("[ot-class]", otClass);

/**
 * Directive `ot-text="reference"`
 * 
 * It inserts text content from {@link Page.event:update}.
 * 
 * @hideconstructor
 */
class otText extends DirectiveBase {
  get name() {
    return "text";
  }

  reset() {
    setText(this.elem, null);
  }

  update(changes) {
    setText(this.elem, changes.pick(this.ref)); 
  }
}

registerDirective("[ot-text]", otText);

/**
 * Directive `ot-img="reference"`
 * 
 * It inserts image element from {@link Page.event:update} inside its host.
 * The value in the Changes should be an instance of created and pre-loaded Image element. 
 * 
 * @hideconstructor
 */
class otImg extends DirectiveBase {
  get name() {
    return "img";
  }

  reset() {
    setChild(this.elem, null);
  }

  update(changes) {
    let img = changes.pick(this.ref);
    if (!!img && !(img instanceof Image)) {
      throw new Error(`Invalid value for image: ${img}`);
    }
    setChild(this.elem, img);
  }
}

registerDirective("[ot-img]", otImg);

/**
 * Directives `ot-attr-something="reference"`
 * 
 * The allowed attributes are: 
 * - `disabled` 
 * - `hidden` 
 * - `height` 
 * - `width` 
 * - `min` 
 * - `max` 
 * - `low` 
 * - `high` 
 * - `optimum` 
 * - `value` 
 * 
 * It deletes or sets value of the attribute to a value from {@link Page.event:update}.
 * 
 * @hideconstructor
 */
class otAttrBase extends DirectiveBase {
  reset() {
    setAttr(this.elem, this.name, null);
  }

  update(changes) {
    setAttr(this.elem, this.name, changes.pick(this.ref));
  }
}

const ALLOWED_ATTRIBS = ["disabled", "hidden", "height", "width", "min", "max", "low", "high", "optimum", "value"];

// create subclass for each attr with static property
// register them as `ot-something`
ALLOWED_ATTRIBS.forEach(attrname => {
  class otAttr extends otAttrBase {
    get name() {
      return attrname;
    }
  }  registerDirective(`[ot-${attrname}]`, otAttr);
});

/**
 * Directive `ot-when="var"`, `ot-when="var==val", ot-when="var===val"`.
 *
 * It shows/hides host element on {@link Page.event:update}. 
 * 
 * The `var` is a page var reference like `game.feedback`, the `val` is a primitive json expression 
 * like "true" (boolean), "42" (number), "'foo'" (string). 
 * 
 * For `ot-when="var"` element shows when the `var` is defined.
 * 
 * For `ot-when="var==val"` element shows when the `var` is defined and equal to the val.
 * 
 * For `ot-when="var===val"` element shows when the `var` is defined and strictly equal to the val.
 * 
 * @hideconstructor
 */
class otWhen extends DirectiveBase {
  get name() {
    return "when";
  }

  init() {
    const when = this.param();
    const match = when.match(/^([\w.]+)((===?)(.+))?$/);
    if (!match) throw new Error(`Invalid expression for when: ${when}`);
    
    const [_0, ref$1, _2, eq, rhs] = match;

    validate(ref$1);
    this.ref = ref$1;
    
    let val = rhs ? JSON.parse(rhs.replaceAll("'", '"')) : null;

    if (eq == '==') {
      this.check = (v) => (v !== undefined) && v == val;
    } else if (eq == '===') {
      this.check = (v) => (v !== undefined) && v === val;
    } else {
      this.check = (v) => (v !== undefined);
    }
  }

  reset() {
    toggleDisplay(this.elem, false);
  }

  update(changes) {
    let value = changes.pick(this.ref);
    let toggle = this.check(value);

    toggleDisplay(this.elem, toggle);
  }
}

registerDirective("[ot-when]", otWhen);

/** Main page.
 *
 * Centeral point of synchronization.
 *
 * Provides utils to fire and handle events.
 *
 * Installs all registered directives, found in html.
 *
 * *NB*: The installation happens only once, directives won't work in dynamically added html code.
 *
 * @property {Phase} phase set of flags indicating common state of directives, `{ display, inputEnabled }`
 */
class Page {
  /**
   * @param {HTMLElement} [body=document.body] the element to attach all the events
   */
  constructor(body) {
    this.body = body || document.body;
    this.phase = {};
    this.init();
  }

  init() {
    let page = this;
    registry.forEach((cls, sel) => {
      this.body.querySelectorAll(sel).forEach((elem) => {
        // console.debug(cls, sel, elem);
        let inst = new cls(page, elem);
        inst.setup();
      });
    });

    this.resetPhase();
    this.emitReset();
  }

  /**
   * Binds an event handler
   *
   * @param {String} type type of an event
   * @param {Function} handler
   * @param {HTMLElement} [target=page.body] an element to bind handler, instead of the page itself
   */
  onEvent(type, handler, target) {
    (target || this.body).addEventListener(type, handler);
  }

  /**
   * Removes event hanfler
   *
   * @param {String} type type of an event
   * @param {Function} handler, previously binded to an event
   * @param {HTMLElement} [target=page.body]
   */
  offEvent(type, handler, target) {
    (target || this.body).removeEventListener(type, handler);
  }

  /**
   * Waits for an event
   *
   * Returns a promise that resolves when an event happen.
   *
   * *NB*: this doesb't catch events happened before the waiting started. For such cases you need to save the promise and await for it later.
   *
   * Example:
   *
   *    await page.waitForEvent('ot.time.out'); // suspend script until timeout emitd
   *
   *    let waiting = page.waitForEvent('ot.timeout'); // start waiting without suspending
   *    // do some work during which a timeout might happen
   *    await waiting; // suspend for an event happend since the 'waiting' created
   *
   * @param {String} type of the event
   * @param {HTMLElement} [target=page.body]
   * @returns {Promise} resolved when event emitd
   */
  waitForEvent(type, target) {
    target = target || this.body;
    return new Promise((resolve) => {
      function listener(event) {
        resolve(event);
        target.removeEventListener(type, listener);
      }
      target.addEventListener(type, listener);
    });
  }

  /**
   * Emits an event.
   *
   * The event is always a `CustomEvent`.
   * To emit built-in events, use built-in `target.dispatchEvent(event)`.
   *
   * @param {String} type type of the event
   * @param {Object} detail any data to attach to the event
   * @param {HTMLElement} [target=page.body] an alternate element to emit at
   */
  emitEvent(type, detail, target) {
    // console.debug("firing", type, detail);
    const event = new CustomEvent(type, { detail });
    target = target || this.body;
    // NB: queueing a task like a normal event, instead of dispatching synchronously
    setTimeout(() => target.dispatchEvent(event));
  }

  /**
   * Emits page reset.
   *
   * @param {string[]} [vars] list of vars being reset, by default only ['game']
   * @fires Page.reset
   */
  emitReset(vars) {
    if (vars === undefined) {
      this.emitEvent("ot.reset", "*");
    } else {
      if (!Array.isArray(vars)) vars = [vars];
      this.emitEvent("ot.reset", vars);
    }
  }

  /**
   * Emits user input.
   *
   * @param {Strinn} name
   * @param {Strinn} value
   * @fires Page.update
   */
  emitInput(name, value) {
    this.emitEvent("ot.input", { name, value });
  }

  /**
   * Emits update.
   *
   * @param {object|Changes} changes
   * @fires Page.update
   */
  emitUpdate(changes) {
    if (!(changes instanceof Changes)) changes = new Changes(changes);
    this.emitEvent("ot.update", changes);
  }

  /**
   * Emits timeout.
   *
   * @fires Schedule.timeout
   */
  emitTimeout(time) {
    this.emitEvent("ot.timeout", time);
  }

  /**
   * Temporary disables inputs.
   *
   * Emits phase event, but doesn't affect current phase.
   *
   * @fires Page.phase
   */
  freezeInputs() {
    this.emitEvent("ot.phase", { inputEnabled: false, _freezing: true });
  }

  /**
   * Reenables inputs.
   *
   * Emits phase event, but doesn't affect current phase.
   * Inputs wont be reenabled, if a phase change happened and disabled inputs.
   *
   * @fires Page.phase
   */
  unfreezeInputs() {
    if (!this.phase.inputEnabled) return;
    this.emitEvent("ot.phase", { inputEnabled: true, _freezing: true });
  }

  /**
   * Switches display directives.
   *
   * Emits phase event, but doesn't affect current phase.
   *
   * @param {String} name matching `ot-display="name"`
   */
  switchDisplay(name) {
    this.emitEvent("ot.phase", { display: name, _switching: true });
  }

  /**
   * Resets page phase.
   *
   * @param {Object} [flags] some additional initial flags
   */
  resetPhase(flags) {
    let phase0 = { display: null, inputEnabled: false };
    if (flags) {
      Object.assign(phase0, flags);
    }
    this.phase = phase0;
    this.emitEvent("ot.phase", { _resetting: true, ...phase0 });
  }

  /**
   * Toggles page phase.
   *
   * The provided flags override existing, unaffected flags are preserved.
   * I.e. `togglePhase({ inputEnabled: true })` keeps current value of `display` flag.
   *
   * @param {Phase} phase set of flags to change
   * @fires Page.phase
   */
  togglePhase(phase) {
    Object.assign(this.phase, phase);
    this.emitEvent("ot.phase", phase); // NB: only changes are signalled
  }

  submit() {
    this.documentQuery("form").submit();
  }
}

/**
 * A page phase flags
 *
 * The set of fields can be extended by anything else needed for custom directives.
 *
 * @typedef {Object} Phase
 * @property {string} [display] to toggle `ot-display` directives
 * @property {bool} [inputEnabled] to enable/disable `ot-input` directives
 */

/**
 * Indicates that a user started a game pressing 'Space' or something.
 * Triggered by directive `ot-ready`
 *
 * @event Page.ready
 * @property {string} type `ot.ready`
 */

/**
 * Indicates that some page vars have been reset
 *
 * @event Page.reset
 * @property {string} type `ot.reset`
 * @property {string[]} detail list of top-level vars
 */

/**
 * Indicates that page variables has changed.
 * Used by directives to update their content.
 *
 * @event Page.update
 * @property {string} type `ot.update`
 * @property {Changes} detail changes
 */

/**
 * Indicates that a user provided some input.
 *
 * @event Page.input
 * @property {string} type `ot.input`
 * @property {object} detail an object like `{field: value}` corresponding to directive `ot-input="field=value"`
 */

/**
 * Indicates a timed phase switching display, inputEnabled, or something else
 *
 * @event Page.phase
 * @property {string} type `ot.phase`
 * @property {object} detail an object like `{display: something, inputEnabled: bool, ...}`
 */

/**
 * Indicates timeout happened.
 *
 * @event Page.timeout
 * @property {string} type `ot.timeout`
 */

/**
 * Game logic
 *
 * Keeps game state and provides some utils to play.
 *
 * The game state is an arbitraty object holding all the data needed to play and display the game.
 * It is initially empty and updated via `update` method, that keeps it in sync with html directives.
 *
 * @property {object} conf constant config vars
 * @property {object} state main game data
 * @property {object} status set of flags indicating game status
 * @property {object} result result data
 * @property {object} error in form of `{ code, message }`
 * @property {number} iteration when in iterations loop
 */
class Game {
  /**
   * @param {Page} page
   */
  constructor(page) {
    this.page = page;
    this.config = {};

    this.trial = {};
    this.status = {};
    this.feedback = undefined;
  }

  /**
   * Sets config and resets game.
   *
   * The page is updated forr 'config' vars.
   *
   * @param {object} config
   * @fires Page.update
   */
  setConfig(config) {
    this.config = config;
    this.page.emitUpdate({ config });
  }

  /**
   * Resets all trial-related data and game state.
   *
   * Sets `trial`, `status`, `feedback` to empty objects or nulls.
   * Updates page with all the affected objects.
   *
   * Calls loadTrial hook.
   *
   * @fires Page.reset
   */
  resetTrial() {
    this.trial = {};
    this.status = {};
    this.feedback = undefined;
    this.page.emitReset(["trial", "status", "feedback"]);
    this.loadTrial();
  }

  /**
   * Sets initial game state.
   *
   * Sets initial trial data and updates page.
   * Calls startTrial hook after page update.
   *
   * @param {Object} trial
   * @fires Page.update
   */
  async setTrial(trial) {
    this.trial = trial;

    this.page.emitUpdate({ trial });
    await this.page.waitForEvent("ot.update"); // make sure the hook is called after page update
    this.startTrial(this.trial);
  }

  /**
   * Updates game state.
   *
   * Applies given changes to game state, using {@link Changes}
   *
   * @param {Object} changes the changes to apply
   * @fires Page.update
   */
  updateTrial(changes) {
    new Changes(changes).patch(this.trial);
    this.page.emitUpdate(new Changes(changes, "trial"));
  }

  /**
   * Sets game status.
   *
   * Provided flags are updated in game.status
   *
   * @param {Object} status
   * @fires Page.update
   * @fires Game.status
   */
  updateStatus(changes) {
    let status = this.status;
    Object.assign(status, changes);
    this.page.emitUpdate({ status: changes });
    this.page.emitEvent("ot.status", changes);
    if (changes.trialStarted) {
      this.page.emitEvent("ot.started");
    }
    if (changes.trialCompleted) {
      this.page.emitEvent("ot.completed");
    }
    if (changes.gameOver) {
      this.page.emitEvent("ot.gameover");
    }
  }

  /**
   * Sets feedback
   *
   * Calls hook onFeedback(feedback)
   *
   * @param {string} code
   * @param {string} message
   * @fires Page.update
   */
  setFeedback(feedback) {
    this.feedback = feedback;
    this.page.emitUpdate({ feedback });
    this.onFeedback(this.feedback);
  }

  /**
   * Clears feedback.
   *
   * @fires Page.reset
   */
  clearFeedback() {
    this.feedback = undefined;
    this.page.emitReset("feedback");
  }

  /**
   * Sets progress
   *
   * Calls hook onProgress(progress)
   *
   * @param {string} code
   * @param {string} message
   * @fires Page.update
   */
  setProgress(progress) {
    this.progress = progress;
    this.page.emitUpdate({ progress });
    this.onProgress(this.progress);
  }

  /**
   * Clears progress.
   *
   * @fires Page.reset
   */
  resetProgress() {
    this.progress = undefined;
    this.page.emitReset("progress");
  }

  /**
   * A hook called to retrieve initial Trial data.
   * Shuld call setTria l
   */
  loadTrial() {
    throw new Error("Implement the `loadTrial` hook");
  }

  /**
   * A hook called after trial loaded.
   *
   * Should start all game process.
   *
   * @param {Object} trial reference to game.trial
   */
  startTrial(trial) {
    throw new Error("Implement the `startTrial` hook");
  }

  /**
   * A hook called when setFeedback
   *
   * @param {Object} feedback reference to game.feedback
   */
  onFeedback(feedback) {}

  /**
   * A hook called after setProgress
   *
   * @param {Object} progress reference to game.progress
   */
  onProgress(progress) {}

  /**
   * A handler for {@link Page.ready}
   *
   * @type {Game~onReady}
   */
  set onReady(fn) {
    this.page.onEvent("ot.ready", (ev) => fn());
  }

  /**
   * A handler for {@link Page.input}
   *
   * @type {Game~onInput}
   */
  set onInput(fn) {
    this.page.onEvent("ot.input", (ev) => fn(ev.detail.name, ev.detail.value));
  }

  /**
   * A handler for {@link Page.phase}
   *
   * Does not get triggered on resetting and temporaty freezing/unfreezing/switching.
   *
   * @type {Game~onPhase}
   */
  set onPhase(fn) {
    this.page.onEvent("ot.phase", (ev) => {
      if (ev.detail._resetting || ev.detail._freezing || ev.detail._switching) return;
      fn(ev.detail);
    });
  }

  /**
   * A handler for {@link Schedule.timeout}
   *
   * @type {Game~onTimeout}
   */
  set onTimeout(fn) {
    this.page.onEvent("ot.timeout", (ev) => fn(ev.detail));
  }

  /**
   * A handler for {@link Game.status}
   *
   * @type {Game~onStatus}
   */
  set onStatus(fn) {
    this.page.onEvent("ot.status", (ev) => fn(this.status, ev.detail));
  }

  /**
   * Plays a game trial.
   *
   * It resets trial and waits for status update with trial_completed
   *
   * @returns {Promise} resolving with result when game completes
   */
  async playTrial() {
    this.resetTrial();
    await this.page.waitForEvent("ot.completed");
  }

  async playIterations() {
    while (!this.status.gameOver) {
      await this.playTrial();
      await sleep(this.config.post_trial_pause);
    }
  }
}

/**
 * A progress during iterations loop.
 *
 * @typedef {object} Progress
 * @property {number|null} total total number of itterations, or null if it's infinite
 * @property {number} current current iteration, counting from 1
 * @property {number} completed number of completed rounds
 * @property {number} solved number of rounds with `success=true`
 * @property {number} failed number of rounds with `success=false`
 */

/**
 * Indicates that a game (or something else) has been reset.
 *
 * @event Game.reset
 * @property {string} type `ot.reset`
 * @property {string} detail an object being reset, i.e. 'game' or 'progress'
 */

/**
 * Indicates a game has started.
 *
 * @event Game.started
 * @property {string} type `ot.started`
 * @property {params} detail some params, like `{ iteration: i }`
 */

/**
 * @callback Game~onStart
 * @param {object} params some staring params such as provided by {@link Game.start}
 */

/**
 * Indicates some game conditions changed.
 *
 * @event Game.status
 * @property {string} type `ot.status`
 * @property {object} detail some flags
 */

/**
 * @callback Game~onStatus
 * @param {object} status some staring params provided by `game.status`
 */

/**
 * Indicates an error (relvant to user) happend.
 *
 * @event Game.error
 * @property {string} type `ot.error`
 * @property {object|null} detail contains `code` and `message`, or null for reseting error
 */

/**
 * @callback Game~onError
 * @param {object} error `{ code, message}`
 */

/**
 * Indicates a game has completed.
 *
 * @event Game.completed
 * @property {string} type `ot.completed`
 * @property {object} detail result data indicating game outcome
 */

/**
 * @callback Game~onCompleted
 * @param {object} result
 */

/**
 * Schedule to toggle page flags at specifed time moments
 */

class Schedule {
  constructor(page) {
    this.page = page;
    this.timers = new Timers();
    this.phases = null;
    this.timeout = null;
  }

  /**
   * Setup schedule
   *
   * The `phases` in config is a list of {@link Phase} augmented with `time` field indicating time in ms to emit phase events.
   * ```
   * { phases: [
   *  { at: 0, display: "something", }
   *  { at: 1000, display: "somethingelse", inputEnabled: false }
   * ]}
   * ```
   *
   * The `timeout` in config is time in ms to emit timeout even t.
   *
   * @param {Object} config an object with `{ phases, timeout }`
   */
  setup(config) {
    this.phases = config.phases;
    this.timeout = config.timeout;
  }

  /**
   * Starts emitting all scheduled events
   */
  start() {
    if (this.phases) {
      this.phases.forEach((phase, i) => {
        const flags = Object.assign({}, phase);
        delete flags.at;

        this.timers.delay(
          `phase-${i}`,
          () => {
            this.page.togglePhase(flags);
          },
          phase.at
        );
      });
    }

    if (this.timeout) {
      this.timers.delay(
        `timeout`,
        () => {
          this.stop();
          this.page.emitTimeout(this.timeout);
        },
        this.timeout
      );
    }
  }

  /**
   * Stops emitting scheduled events
   */
  stop() {
    this.timers.cancel();
  }
}

const otree = {
  dom, random, changes, timers, measurement, 
  DirectiveBase, registerDirective
};

window.addEventListener('load', function() {
  otree.page = new Page(document.body);
  otree.game = new Game(otree.page);
  otree.schedule = new Schedule(otree.page);

  if (!window.main) {
    throw new Error("You need to define global `function main()` to make otree work");
  }
  window.main();
});

window.otree = otree;

export { otree };
