/**
 * Unit tests for the useAuth composable.
 *
 * Network calls ($fetch) are fully mocked so tests run without a live backend.
 * Nuxt auto-imports (useCookie, useRuntimeConfig, useRouter) are stubbed in
 * tests/setup.ts.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { ref } from "vue";
import { useAuth } from "../composables/useAuth";
import type { User, TokenResponse } from "../types/auth";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const mockUser: User = {
  id: 1,
  email: "captain@example.com",
  username: "captain1",
  full_name: "Test Captain",
  role: "CAPTAIN" as any,
  is_active: true,
  is_superuser: false,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
};

const mockTokenResponse: TokenResponse = {
  access_token: "test.jwt.token",
  token_type: "bearer",
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Re-initialise useCookie stub so each test starts with a clean token state.
 * The composable captures the ref returned by useCookie on creation, so we
 * must replace the stub *before* calling useAuth().
 */
function resetCookieStub(initialValue: string | null = null) {
  const cookieRef = ref<string | null>(initialValue);
  vi.stubGlobal("useCookie", () => cookieRef);
  return cookieRef;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("useAuth — isAuthenticated", () => {
  it("returns false when no token is stored", () => {
    resetCookieStub(null);
    const { isAuthenticated } = useAuth();
    expect(isAuthenticated.value).toBe(false);
  });

  it("returns true when a token exists in the cookie", () => {
    resetCookieStub("some.jwt.token");
    const { isAuthenticated } = useAuth();
    expect(isAuthenticated.value).toBe(true);
  });
});

describe("useAuth — role computed properties", () => {
  it("isCaptain is true for a captain user", () => {
    resetCookieStub("token");
    const auth = useAuth();
    auth.user.value = mockUser;
    expect(auth.isCaptain.value).toBe(true);
    expect(auth.isPlayer.value).toBe(false);
    expect(auth.isReferee.value).toBe(false);
  });

  it("isPlayer is true for a player user", () => {
    resetCookieStub("token");
    const auth = useAuth();
    auth.user.value = { ...mockUser, role: "PLAYER" as any };
    expect(auth.isPlayer.value).toBe(true);
    expect(auth.isCaptain.value).toBe(false);
  });

  it("isReferee is true for a referee user", () => {
    resetCookieStub("token");
    const auth = useAuth();
    auth.user.value = { ...mockUser, role: "REFEREE" as any };
    expect(auth.isReferee.value).toBe(true);
  });

  it("all role flags are false when no user is set", () => {
    resetCookieStub(null);
    const auth = useAuth();
    auth.user.value = null;
    expect(auth.isPlayer.value).toBe(false);
    expect(auth.isCaptain.value).toBe(false);
    expect(auth.isReferee.value).toBe(false);
  });
});

describe("useAuth — hasRole", () => {
  it("returns true when user has one of the allowed roles", () => {
    resetCookieStub("token");
    const auth = useAuth();
    auth.user.value = mockUser; // CAPTAIN
    expect(auth.hasRole("CAPTAIN", "REFEREE").value).toBe(true);
  });

  it("returns false when user role is not in the allowed list", () => {
    resetCookieStub("token");
    const auth = useAuth();
    auth.user.value = { ...mockUser, role: "PLAYER" as any };
    expect(auth.hasRole("CAPTAIN", "REFEREE").value).toBe(false);
  });

  it("returns false when no user is logged in", () => {
    resetCookieStub(null);
    const auth = useAuth();
    auth.user.value = null;
    expect(auth.hasRole("CAPTAIN").value).toBe(false);
  });
});

describe("useAuth — login", () => {
  beforeEach(() => {
    resetCookieStub(null);
  });

  it("stores the token and returns success on valid credentials", async () => {
    vi.stubGlobal(
      "$fetch",
      vi
        .fn()
        .mockResolvedValueOnce(mockTokenResponse) // POST /auth/login
        .mockResolvedValueOnce(mockUser)          // GET  /auth/me
    );

    const auth = useAuth();
    const result = await auth.login({ username: "captain1", password: "secret" });

    expect(result.success).toBe(true);
    expect(auth.token.value).toBe("test.jwt.token");
    expect(auth.user.value?.username).toBe("captain1");
  });

  it("returns failure with error message on bad credentials", async () => {
    vi.stubGlobal(
      "$fetch",
      vi.fn().mockRejectedValue({ data: { detail: "Incorrect username or password" } })
    );

    const auth = useAuth();
    const result = await auth.login({ username: "wrong", password: "wrong" });

    expect(result.success).toBe(false);
    expect(result.error).toBe("Incorrect username or password");
  });
});

describe("useAuth — logout", () => {
  it("clears the token and user, then redirects to /auth/login", async () => {
    const routerPush = vi.fn();
    vi.stubGlobal("useRouter", () => ({ push: routerPush }));

    vi.stubGlobal("$fetch", vi.fn().mockResolvedValue({})); // logout endpoint

    resetCookieStub("existing.token");
    const auth = useAuth();
    auth.user.value = mockUser;

    await auth.logout();

    expect(auth.token.value).toBeNull();
    expect(auth.user.value).toBeNull();
    expect(routerPush).toHaveBeenCalledWith("/auth/login");
  });
});
