import React, {
  type ReactNode,
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { type User, onAuthStateChanged } from "firebase/auth";

import { auth } from "@/firebase-config";
import { authService } from "@/services/auth-service";

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  signUp: (email: string, password: string, name: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
      setUser(firebaseUser);
      setIsLoading(false);
    });
    return unsubscribe;
  }, []);

  const value: AuthContextValue = {
    user,
    isLoading,
    signUp: async (email, password, name) => {
      await authService.signUp(email, password, name);
    },
    signIn: async (email, password) => {
      await authService.signIn(email, password);
    },
    signOut: async () => {
      await authService.signOut();
    },
    deleteAccount: async () => {
      await authService.deleteAccount(user!);
    },
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuthContext must be used within <AuthProvider>");
  }
  return ctx;
}
