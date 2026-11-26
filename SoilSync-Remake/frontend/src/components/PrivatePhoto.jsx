import React, { useEffect, useState } from "react";
import { privatePhoto } from "../services/api";

export default function PrivatePhoto({ path, alt, className }) {
  const [image, setImage] = useState({ path: "", url: "", error: "" });
  useEffect(() => {
    const controller = new AbortController();
    let url;
    privatePhoto(path, controller.signal)
      .then((blob) => {
        if (controller.signal.aborted) return;
        url = URL.createObjectURL(blob);
        setImage({ path, url, error: "" });
      })
      .catch((error) => {
        if (!controller.signal.aborted)
          setImage({ path, url: "", error: error.message });
      });
    return () => {
      controller.abort();
      if (url) URL.revokeObjectURL(url);
    };
  }, [path]);
  if (image.path !== path || !image.url)
    return (
      <p role="status">
        {image.path === path && image.error
          ? image.error
          : "Loading your private photo…"}
      </p>
    );
  return <img src={image.url} alt={alt} className={className} />;
}
