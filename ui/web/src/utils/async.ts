export interface BoundedTask<T> {
  key: string;
  run: () => Promise<T>;
}

export interface BoundedTaskResult<T> {
  key: string;
  value?: T;
  error?: string;
  durationMs: number;
}

/**
 * Execute browser tasks with an explicit concurrency ceiling.
 * This prevents a local-first page from opening a burst of protected API
 * requests that all perform policy/observability persistence concurrently.
 */
export async function runBounded<T>(
  tasks: Array<BoundedTask<T>>,
  concurrency = 2,
  onResult?: (result: BoundedTaskResult<T>) => void
): Promise<Array<BoundedTaskResult<T>>> {
  const limit = Math.max(1, Math.min(Math.trunc(concurrency), 8));
  const results: Array<BoundedTaskResult<T>> = new Array(tasks.length);
  let cursor = 0;

  async function worker(): Promise<void> {
    while (true) {
      const index = cursor;
      cursor += 1;
      const task = tasks[index];
      if (!task) return;
      const started = performance.now();
      let result: BoundedTaskResult<T>;
      try {
        result = {
          key: task.key,
          value: await task.run(),
          durationMs: Math.round(performance.now() - started),
        };
      } catch (error) {
        result = {
          key: task.key,
          error: error instanceof Error ? error.message : String(error),
          durationMs: Math.round(performance.now() - started),
        };
      }
      results[index] = result;
      onResult?.(result);
    }
  }

  await Promise.all(
    Array.from({ length: Math.min(limit, tasks.length) }, () => worker())
  );
  return results;
}
