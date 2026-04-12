// Global test setup — mocks Nuxt auto-imports that are unavailable outside
// the Nuxt dev server / build context.
import { vi } from "vitest";
import { ref, computed } from "vue";

// Nuxt composable stubs

// useCookie — returns a plain reactive ref so composables can read/write it.
vi.stubGlobal("useCookie", (_key: string, _opts?: unknown) => ref<string | null>(null));

// useRuntimeConfig — returns the minimal shape useAuth reads.
vi.stubGlobal("useRuntimeConfig", () => ({
  public: { apiBaseUrl: "http://localhost:8000/api/v1" },
}));

// useRouter — returns a minimal router stub.
vi.stubGlobal("useRouter", () => ({
  push: vi.fn(),
}));

// $fetch — returns a rejected promise by default; individual tests override it.
vi.stubGlobal("$fetch", vi.fn().mockRejectedValue(new Error("$fetch not mocked")));
