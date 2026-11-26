import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { figma } from "../data/figma";

export function FIcon({ page = "home", index = 0, className = "", alt = "" }) {
  const asset = figma[page][index];
  return (
    <img
      src={asset.src}
      width={asset.width || undefined}
      height={asset.height || undefined}
      className={`figma-icon ${className}`}
      alt={alt}
    />
  );
}
export function Badge({ children, dark = false }) {
  return (
    <span className={`badge ${dark ? "badge-dark" : ""}`}>{children}</span>
  );
}
export function Heading({ icon: Icon, title, aside }) {
  return (
    <div className="section-heading">
      <h2>
        {Icon && <Icon size={21} aria-hidden="true" />}
        {title}
      </h2>
      {aside && <small>{aside}</small>}
    </div>
  );
}
export function Dialog({ title, children, onClose }) {
  const ref = useRef(null),
    previous = useRef(document.activeElement);
  useEffect(() => {
    const dialog = ref.current;
    dialog.showModal();
    const trigger = previous.current;
    return () => {
      dialog.close();
      trigger?.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="dialog"
      onCancel={(event) => {
        event.preventDefault();
        onClose();
      }}
      aria-labelledby="dialog-title"
    >
      <div className="dialog-heading">
        <h2 id="dialog-title">{title}</h2>
        <button
          type="button"
          className="icon-button"
          aria-label="Close dialog"
          onClick={onClose}
        >
          <X size={22} />
        </button>
      </div>
      {children}
    </dialog>
  );
}
export function PreviewNote({ children }) {
  return (
    <p className="preview-note">
      {children || "Frontend preview · saved on this device only"}
    </p>
  );
}
