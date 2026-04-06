import {
  EmailAuthProvider,
  type User,
  createUserWithEmailAndPassword,
  reauthenticateWithCredential,
  sendPasswordResetEmail,
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

  sendPasswordReset: (email: string) => {
    return sendPasswordResetEmail(auth, email);
  },

  // re-auth is required by Firebase before sensitive operations
  reauthenticate: (user: User, password: string) => {
    const credential = EmailAuthProvider.credential(user.email!, password);
    return reauthenticateWithCredential(user, credential);
  },

  updateEmail: (user: User, newEmail: string) => {
    return updateEmail(user, newEmail);
  },

  updatePassword: (user: User, newPassword: string) => {
    return updatePassword(user, newPassword);
  },
};
