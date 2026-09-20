import { useEffect, useRef, useState } from "react";

interface EditableTextProps {
  value: string;
  placeholder?: string;
  onSave: (newValue: string) => void;
  multiline?: boolean;
  className?: string;
  inputClassName?: string;
  onClick?: (e: React.MouseEvent) => void;
  /** Externally-controlled edit mode, for a caller that starts editing from its own
   * trigger (e.g. a separate icon button) instead of a click on the displayed text —
   * e.g. Sidebar's rename, where the text itself must stay a normal navigation link.
   * When omitted, the component manages its own click-to-edit state as before. */
  editing?: boolean;
  onEditingChange?: (editing: boolean) => void;
}

export function EditableText({
  value,
  placeholder,
  onSave,
  multiline,
  className,
  inputClassName,
  onClick,
  editing: controlledEditing,
  onEditingChange,
}: EditableTextProps) {
  const isControlled = controlledEditing !== undefined;
  const [internalEditing, setInternalEditing] = useState(false);
  const editing = isControlled ? controlledEditing : internalEditing;
  const [draft, setDraft] = useState(value);
  // Unmounting the focused input (which setEditing(false) triggers, from either
  // commit or cancel) fires a native blur that re-invokes onBlur=commit a second
  // time — this guards against that double-firing a duplicate onSave/mutate call.
  const settledRef = useRef(false);

  // In controlled mode, editing is switched on from outside this component (e.g. a
  // pencil-icon click sets the parent's own state) — sync the draft at that point,
  // same as startEditing does for the uncontrolled/click-to-edit case.
  useEffect(() => {
    if (editing) settledRef.current = false;
    if (isControlled && editing) setDraft(value);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editing]);

  function setEditing(next: boolean) {
    if (isControlled) onEditingChange?.(next);
    else setInternalEditing(next);
  }

  function startEditing(e: React.MouseEvent) {
    onClick?.(e);
    setDraft(value);
    setEditing(true);
  }

  function commit() {
    if (settledRef.current) return;
    settledRef.current = true;
    setEditing(false);
    if (draft !== value) onSave(draft);
  }

  function cancel() {
    if (settledRef.current) return;
    settledRef.current = true;
    setDraft(value);
    setEditing(false);
  }

  if (editing) {
    const inputProps = {
      value: draft,
      autoFocus: true,
      onBlur: commit,
      // Guards against a caller (like Sidebar) rendering this inside a clickable
      // ancestor (a nav Link) — a click while editing shouldn't trigger it. Both
      // calls are needed: stopPropagation alone doesn't stop the anchor's own
      // native navigate-on-click default action.
      onClick: (e: React.MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
      },
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
        setDraft(e.target.value),
      onKeyDown: (e: React.KeyboardEvent) => {
        if (e.key === "Escape") cancel();
        if (e.key === "Enter" && (!multiline || e.metaKey || e.ctrlKey)) {
          e.preventDefault();
          commit();
        }
      },
      className: inputClassName ?? className,
    };
    return multiline ? <textarea {...inputProps} rows={3} /> : <input {...inputProps} />;
  }

  return (
    <span
      onClick={isControlled ? onClick : startEditing}
      className={`${isControlled ? "" : "cursor-text"} ${!value ? "text-faint" : ""} ${className ?? ""}`}
    >
      {value || placeholder || "Click to set"}
    </span>
  );
}
