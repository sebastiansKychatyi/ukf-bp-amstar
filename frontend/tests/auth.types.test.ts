/**
 * Tests for auth type definitions and role enumeration.
 *
 * These tests verify that the UserRole enum values match what the backend
 * API returns, preventing silent contract mismatches.
 */

import { describe, it, expect } from "vitest";
import { UserRole } from "../types/auth";

describe("UserRole enum", () => {
  it("defines PLAYER role", () => {
    expect(UserRole.PLAYER).toBe("PLAYER");
  });

  it("defines CAPTAIN role", () => {
    expect(UserRole.CAPTAIN).toBe("CAPTAIN");
  });

  it("defines REFEREE role", () => {
    expect(UserRole.REFEREE).toBe("REFEREE");
  });

  it("has exactly three roles", () => {
    const roles = Object.values(UserRole);
    expect(roles).toHaveLength(3);
  });

  it("all role values are uppercase strings (matches backend enum)", () => {
    Object.values(UserRole).forEach((role) => {
      expect(role).toBe(role.toUpperCase());
    });
  });
});
