import {
  type User,
  createUserWithEmailAndPassword,
  deleteUser,
  signInWithEmailAndPassword,
  signOut,
  updateEmail,
  updatePassword,
  updateProfile,
} from "firebase/auth";

import { auth } from "@/firebase-config";

export const authService = {
  signUp: (email: string, password: string, name: string) => {
    return createUserWithEmailAndPassword(auth, email, password).then(
      (userCredential) => {
        const user = userCredential.user;
        return updateProfile(user, { displayName: name });
      },
    );
  },

  signIn: (email: string, password: string) => {
    return signInWithEmailAndPassword(auth, email, password);
  },

  signOut: () => {
    return signOut(auth);
  },

  updateEmail: (user: User, newEmail: string) => {
    return updateEmail(user, newEmail);
  },

  updatePassword: (user: User, newPassword: string) => {
    return updatePassword(user, newPassword);
  },

  deleteAccount: (user: User) => {
    return deleteUser(user);
  },
};
