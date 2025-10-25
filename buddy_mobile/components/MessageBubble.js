// buddy/buddy_mobile/components/MessageBubble.js
import React from "react";
import { View, Text, StyleSheet } from "react-native";

export default function MessageBubble({ text, sender, emotion }) {
  return (
    <View
      style={[
        styles.bubble,
        sender === "You" ? styles.userBubble : styles.buddyBubble,
      ]}
    >
      <Text style={styles.sender}>
        {sender}
        {emotion ? ` (${emotion})` : ""}:
      </Text>
      <Text style={styles.text}>{text}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  bubble: {
    maxWidth: "80%",
    padding: 10,
    borderRadius: 10,
    marginVertical: 5,
  },
  userBubble: {
    backgroundColor: "#007AFF",
    alignSelf: "flex-end",
  },
  buddyBubble: {
    backgroundColor: "#e5e5ea",
    alignSelf: "flex-start",
  },
  sender: {
    fontWeight: "bold",
    marginBottom: 3,
    color: "#000",
  },
  text: {
    color: "#000",
  },
});
