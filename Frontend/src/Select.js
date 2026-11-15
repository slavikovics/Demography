import { useCallback, useEffect, useId, useRef, useState } from 'react';
import './Select.css';

function Chevron({ open }) {
  return (
    <svg className={`select__chevron${open ? ' select__chevron--open' : ''}`} width="16" height="16"
         viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path d="M3.5 6l4.5 4.5L12.5 6" fill="none" stroke="currentColor" strokeWidth="1.8"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Check() {
  return (
    <svg className="select__check" width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="2"
            strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/**
 * Доступный выпадающий список (combobox + listbox) с группами опций.
 * options: [{ value, label, group? }] — опции одной группы должны идти подряд.
 */
export default function Select({ label, value, options, onChange, disabled = false, className = '', menuAlign = 'left' }) {
  const uid = useId();
  const rootRef = useRef(null);
  const buttonRef = useRef(null);
  const listRef = useRef(null);
  const typeahead = useRef({ text: '', timer: null });

  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);

  const selectedIndex = options.findIndex((option) => option.value === value);
  const selected = options[selectedIndex];

  const openMenu = useCallback(() => {
    setActive(selectedIndex >= 0 ? selectedIndex : 0);
    setOpen(true);
  }, [selectedIndex]);

  // закрытие по клику вне списка
  useEffect(() => {
    if (!open) return undefined;
    const onPointerDown = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onPointerDown);
    document.addEventListener('touchstart', onPointerDown);
    return () => {
      document.removeEventListener('mousedown', onPointerDown);
      document.removeEventListener('touchstart', onPointerDown);
    };
  }, [open]);

  // активная опция всегда в зоне видимости
  useEffect(() => {
    if (!open || active < 0) return;
    listRef.current?.querySelector(`[data-index="${active}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [open, active]);

  useEffect(() => () => clearTimeout(typeahead.current.timer), []);

  const choose = (index) => {
    const option = options[index];
    if (!option) return;
    onChange(option.value);
    setOpen(false);
    buttonRef.current?.focus();
  };

  const findByPrefix = (prefix) => {
    const text = prefix.toLowerCase();
    const from = open ? active + 1 : selectedIndex + 1;
    const ordered = [...options.keys()].map((_, i) => (from + i) % options.length);
    return ordered.find((i) => options[i].label.toLowerCase().startsWith(text));
  };

  const onKeyDown = (event) => {
    if (disabled) return;
    const last = options.length - 1;

    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        if (!open) openMenu();
        else setActive((i) => Math.min(last, i + 1));
        break;
      case 'ArrowUp':
        event.preventDefault();
        if (!open) openMenu();
        else setActive((i) => Math.max(0, i - 1));
        break;
      case 'Home':
        if (open) { event.preventDefault(); setActive(0); }
        break;
      case 'End':
        if (open) { event.preventDefault(); setActive(last); }
        break;
      case 'Enter':
      case ' ':
        event.preventDefault();
        if (open) choose(active);
        else openMenu();
        break;
      case 'Escape':
        if (open) { event.preventDefault(); setOpen(false); }
        break;
      case 'Tab':
        setOpen(false);
        break;
      default:
        if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
          clearTimeout(typeahead.current.timer);
          typeahead.current.text += event.key;
          typeahead.current.timer = setTimeout(() => { typeahead.current.text = ''; }, 600);
          const match = findByPrefix(typeahead.current.text);
          if (match !== undefined) {
            if (open) setActive(match);
            else onChange(options[match].value);
          }
        }
    }
  };

  let lastGroup;

  return (
    <div className={`select ${className}`} ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className={`select__button${open ? ' select__button--open' : ''}`}
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={`${uid}-list`}
        aria-activedescendant={open && active >= 0 ? `${uid}-opt-${active}` : undefined}
        aria-label={`${label}: ${selected?.label ?? ''}`}
        disabled={disabled}
        onClick={() => (open ? setOpen(false) : openMenu())}
        onKeyDown={onKeyDown}
      >
        <span className="select__text">
          <span className="select__caption">{label}</span>
          <span className="select__value">{selected?.label ?? '—'}</span>
        </span>
        <Chevron open={open} />
      </button>

      {open && (
        <div
          ref={listRef}
          id={`${uid}-list`}
          role="listbox"
          aria-label={label}
          className={`select__menu select__menu--${menuAlign}`}
        >
          {options.map((option, index) => {
            const showGroup = option.group && option.group !== lastGroup;
            lastGroup = option.group;
            return (
              <div key={option.value} role="presentation">
                {showGroup && <div className="select__group" role="presentation">{option.group}</div>}
                <div
                  id={`${uid}-opt-${index}`}
                  data-index={index}
                  role="option"
                  aria-selected={option.value === value}
                  className={
                    'select__option'
                    + (option.value === value ? ' select__option--selected' : '')
                    + (index === active ? ' select__option--active' : '')
                  }
                  onMouseEnter={() => setActive(index)}
                  onMouseDown={(event) => event.preventDefault()}
                  onClick={() => choose(index)}
                >
                  <span className="select__option-label">{option.label}</span>
                  {option.value === value && <Check />}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
