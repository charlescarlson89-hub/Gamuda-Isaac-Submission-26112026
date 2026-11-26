import React, { useState } from "react";
import {
  Camera,
  ImagePlus,
  LoaderCircle,
  SwitchCamera,
  X,
  ZapOff,
} from "lucide-react";

export default function CameraStage({
  camera,
  title = "SNAP WASTE",
  hint = "CENTER YOUR FOOD SCRAPS",
  onClose,
  onCapture,
  analysePhoto = true,
  processing = false,
}) {
  const [zoom, setZoom] = useState(1);
  return (
    <section
      className="capture-stage"
      aria-label="Camera"
      aria-busy={processing}
    >
      {camera.stream && (
        <video
          ref={camera.video}
          autoPlay
          muted
          playsInline
          style={{ transform: `scale(${zoom})` }}
          aria-label="Live camera preview"
        />
      )}
      <div className="camera-grid" aria-hidden="true" />
      <div className="camera-topbar">
        <button
          type="button"
          className="camera-icon"
          onClick={onClose}
          aria-label="Close camera"
        >
          <X size={21} />
        </button>
        <h1>
          <i />
          {title}
        </h1>
        <button
          type="button"
          className="camera-icon"
          disabled
          aria-label="Flash unavailable"
        >
          <ZapOff size={21} />
        </button>
      </div>
      <div className="capture-reticle" aria-hidden="true">
        <i />
        <i />
        <i />
        <i />
        <span>{hint}</span>
      </div>
      {(camera.error || processing) && (
        <div className="capture-feedback" role="status">
          {processing ? (
            <>
              <LoaderCircle className="scan-spinner" /> Identifying your scraps…
            </>
          ) : (
            camera.error
          )}
        </div>
      )}
      <div className="capture-stage-controls">
        <div className="camera-zoom">
          {[1, 2].map((level) => (
            <button
              type="button"
              key={level}
              aria-pressed={zoom === level}
              onClick={() => setZoom(level)}
            >
              {level}x
            </button>
          ))}
        </div>
        <div className="capture-buttons">
          <button
            className="camera-gallery"
            type="button"
            aria-label="Choose a waste photo"
            onClick={() => camera.input.current?.click()}
            disabled={processing}
          >
            <ImagePlus size={23} />
          </button>
          <button
            className="shutter"
            type="button"
            disabled={camera.busy || processing}
            aria-label={
              camera.stream
                ? analysePhoto ? "Capture photo and analyse with Google AI" : "Capture photo"
                : "Open camera"
            }
            onClick={() => (onCapture ? onCapture(zoom) : camera.capture(zoom))}
          >
            <span>
              {camera.busy && (
                <LoaderCircle className="scan-spinner" size={22} />
              )}
            </span>
          </button>
          <button
            className="camera-gallery"
            type="button"
            disabled={!camera.stream || processing}
            onClick={camera.flip}
            aria-label="Switch camera"
          >
            <SwitchCamera size={23} />
          </button>
        </div>
        <span>
          {camera.busy
            ? "Opening camera…"
            : camera.stream
              ? "Tap to Capture"
              : "Tap to Open Camera"}
        </span>
        <small>{analysePhoto ? "Photos are analysed by Google AI." : "Your photo is saved privately."}</small>
      </div>
      {!camera.stream && !camera.error && !camera.busy && (
        <Camera
          className="camera-empty-icon"
          size={35}
          strokeWidth={1}
          aria-hidden="true"
        />
      )}
    </section>
  );
}
