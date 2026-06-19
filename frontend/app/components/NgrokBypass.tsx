"use client";
import { useEffect } from "react";

export default function NgrokBypass() {
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      let [resource, config] = args;
      if (!config) config = {};
      if (!config.headers) config.headers = {};
      
      const headers = new Headers(config.headers);
      headers.set('ngrok-skip-browser-warning', '69420');
      
      config.headers = headers;
      return originalFetch(resource, config);
    };
  }, []);
  
  return null;
}
