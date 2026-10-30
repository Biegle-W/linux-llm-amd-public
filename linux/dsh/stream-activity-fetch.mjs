// Observe transport activity without modifying the provider's response bytes.
export function activityFetch(pulse, fetchImpl = globalThis.fetch) {
  return async (input, init) => {
    const response = await fetchImpl(input, init);
    pulse();
    if (response.body === null) return response;
    const observed = response.body.pipeThrough(new TransformStream({
      transform(chunk, controller) {
        if (chunk.byteLength > 0) pulse();
        controller.enqueue(chunk);
      },
    }));
    const wrapped = new Response(observed, {
      status: response.status,
      statusText: response.statusText,
      headers: response.headers,
    });
    for (const key of ['url', 'redirected', 'type']) {
      Object.defineProperty(wrapped, key, { value: response[key] });
    }
    return wrapped;
  };
}
