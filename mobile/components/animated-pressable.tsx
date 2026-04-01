import { Pressable, PressableProps, StyleProp, ViewStyle } from "react-native";
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from "react-native-reanimated";

const AnimatedPressableBase = Animated.createAnimatedComponent(Pressable);

interface AnimatedPressableProps extends PressableProps {
  scaleTo?: number;
  style?: StyleProp<ViewStyle>;
  className?: string;
}

export function AnimatedPressable({
  scaleTo = 0.95,
  onPressIn,
  onPressOut,
  style,
  children,
  ...rest
}: AnimatedPressableProps) {
  const scale = useSharedValue(1);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <AnimatedPressableBase
      onPressIn={(e) => {
        scale.value = withSpring(scaleTo);
        onPressIn?.(e);
      }}
      onPressOut={(e) => {
        scale.value = withSpring(1);
        onPressOut?.(e);
      }}
      style={[style, animatedStyle]}
      {...rest}
    >
      {children}
    </AnimatedPressableBase>
  );
}
