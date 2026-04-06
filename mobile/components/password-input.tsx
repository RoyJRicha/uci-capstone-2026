import { MaterialIcons } from "@expo/vector-icons";

import { Pressable, TextInput, TextInputProps, View } from "react-native";

import React, { forwardRef, useState } from "react";

type PasswordInputProps = Omit<TextInputProps, "secureTextEntry">;

export const PasswordInput = forwardRef<TextInput, PasswordInputProps>(
  (props, ref) => {
    const [isVisible, setIsVisible] = useState(false);

    return (
      <View className="flex-row items-center">
        <TextInput
          ref={ref}
          {...props}
          secureTextEntry={!isVisible}
          className="font-body text-on-surface flex-1 py-3 pr-21 pl-3 text-sm"
        />
        <Pressable
          onPress={() => setIsVisible((prev) => !prev)}
          className="absolute right-12.5 p-1"
          accessibilityLabel={isVisible ? "Hide password" : "Show password"}
          accessibilityRole="button"
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <MaterialIcons
            name={isVisible ? "visibility" : "visibility-off"}
            size={20}
            color="rgba(114,119,132,0.7)"
          />
        </Pressable>
      </View>
    );
  },
);

PasswordInput.displayName = "PasswordInput";
