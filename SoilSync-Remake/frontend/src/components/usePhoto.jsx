import React, { useCallback, useEffect, useRef, useState } from "react";

export default function usePhoto({ autoStart = false } = {}) {
  const [photo, setPhotoUrl] = useState(""),
    [stream, setStream] = useState(null),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const facing = useRef("environment");
  const [file, setFile] = useState(null);
  const setPhoto = useCallback((value) => {
    setPhotoUrl(value);
    if (!value) setFile(null);
  }, []);
  const video = useRef(null),
    input = useRef(null),
    activeStream = useRef(null),
    mounted = useRef(true),
    pending = useRef(false);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      activeStream.current?.getTracks().forEach((track) => track.stop());
    };
  }, []);
  useEffect(() => {
    if (stream && video.current) {
      video.current.srcObject = stream;
      video.current
        .play()
        .catch(() =>
          setError("Tap the camera control to try again, or choose a photo."),
        );
    }
  }, [stream]);
  useEffect(
    () => () => {
      if (photo) URL.revokeObjectURL(photo);
    },
    [photo],
  );
  const stop = useCallback(() => {
    activeStream.current?.getTracks().forEach((track) => track.stop());
    activeStream.current = null;
    setStream(null);
  }, []);
  const start = useCallback(
    async (nextFacing = facing.current) => {
      if (pending.current) return;
      pending.current = true;
      setBusy(true);
      setError("");
      stop();
      try {
        if (!navigator.mediaDevices?.getUserMedia)
          throw new Error(
            "Camera access needs HTTPS or localhost. Choose a photo instead.",
          );
        const next = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: nextFacing }, width: { ideal: 1280 } },
          audio: false,
        });
        if (!mounted.current || document.hidden) {
          next.getTracks().forEach((track) => track.stop());
          return;
        }
        activeStream.current = next;
        setStream(next);
        facing.current = nextFacing;
        setPhoto("");
      } catch (err) {
        if (mounted.current)
          setError(
            err.name === "NotAllowedError"
              ? "Camera access was not allowed. You can choose a photo instead."
              : err.message ||
                  "The camera is unavailable. Choose a photo instead.",
          );
      } finally {
        pending.current = false;
        if (mounted.current) setBusy(false);
      }
    },
    [setPhoto, stop],
  );
  useEffect(() => {
    if (autoStart) void start();
  }, [autoStart, start]);
  useEffect(() => {
    const onVisibility = () => {
      if (document.hidden) stop();
    };
    document.addEventListener("visibilitychange", onVisibility);
    return () => document.removeEventListener("visibilitychange", onVisibility);
  }, [stop]);
  async function choose(chosen) {
    if (!chosen) return;
    if (
      !["image/jpeg", "image/png", "image/webp"].includes(chosen.type) ||
      chosen.size > 6 * 1024 * 1024
    ) {
      setError("Choose a JPEG, PNG or WebP photo under 6 MB.");
      return;
    }
    setError("");
    stop();
    setBusy(true);
    let bitmap;
    try {
      bitmap = await createImageBitmap(chosen);
      if (bitmap.width * bitmap.height > 20_000_000)
        throw new Error("Choose a photo under 20 megapixels.");
      const scale = Math.min(1, 1600 / Math.max(bitmap.width, bitmap.height));
      const canvas = document.createElement("canvas");
      canvas.width = Math.round(bitmap.width * scale);
      canvas.height = Math.round(bitmap.height * scale);
      canvas
        .getContext("2d")
        .drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      // Keep multipart requests below the host's 4.5 MB limit and remove photo metadata.
      const blob = await new Promise((resolve) =>
        canvas.toBlob(resolve, "image/jpeg", 0.85),
      );
      if (!blob || blob.size > 3 * 1024 * 1024)
        throw new Error("Choose a smaller photo and try again.");
      if (mounted.current) {
        setFile(new File([blob], "scraps-photo.jpg", { type: "image/jpeg" }));
        setPhoto(URL.createObjectURL(blob));
      }
    } catch (error) {
      if (mounted.current)
        setError(
          error.message ||
            "This photo could not be opened. Choose another photo.",
        );
    } finally {
      bitmap?.close();
      if (mounted.current) setBusy(false);
    }
  }
  async function capture(zoom = 1) {
    if (!stream) {
      await start();
      return;
    }
    const view = video.current;
    if (!view?.videoWidth) {
      setError("The camera is warming up. Try again in a moment.");
      return;
    }
    const canvas = document.createElement("canvas");
    canvas.width = Math.min(1280, view.videoWidth / zoom);
    canvas.height = (canvas.width * view.videoHeight) / view.videoWidth;
    const width = view.videoWidth / zoom,
      height = view.videoHeight / zoom;
    canvas
      .getContext("2d")
      .drawImage(
        view,
        (view.videoWidth - width) / 2,
        (view.videoHeight - height) / 2,
        width,
        height,
        0,
        0,
        canvas.width,
        canvas.height,
      );
    const blob = await new Promise((resolve) =>
      canvas.toBlob(resolve, "image/jpeg", 0.85),
    );
    if (blob && mounted.current) {
      stop();
      setFile(new File([blob], "camera-photo.jpg", { type: "image/jpeg" }));
      setPhoto(URL.createObjectURL(blob));
    }
  }
  const fileInput = (
    <input
      ref={input}
      className="sr-only"
      aria-label="Choose a photo"
      type="file"
      accept="image/jpeg,image/png,image/webp"
      onChange={(event) => {
        choose(event.target.files?.[0]);
        event.target.value = "";
      }}
    />
  );
  return {
    photo,
    file,
    setPhoto,
    stream,
    error,
    busy,
    video,
    input,
    start,
    stop,
    capture,
    fileInput,
    flip: () =>
      start(facing.current === "environment" ? "user" : "environment"),
  };
}
