import React, { useState, useEffect, useRef } from 'react';
import { View, TextInput, Text, ScrollView, TouchableOpacity, KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
// import * as FileSystem from 'expo-file-system';
import { Audio } from 'expo-av';
import * as FileSystem from 'expo-file-system/legacy';
import MessageBubble from "./components/MessageBubble";

const AUDIO_FOLDER = FileSystem.cacheDirectory + "buddy_audio/";
const MAX_CACHE = 5; // keep last 5 files

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [ws, setWs] = useState(null);
  const scrollViewRef = useRef();
  const soundRef = useRef(null);

  useEffect(() => {
    // ensure folder exists
    (async () => {
      try {
        const folderInfo = await FileSystem.getInfoAsync(AUDIO_FOLDER);
        if (!folderInfo.exists) {
          await FileSystem.makeDirectoryAsync(AUDIO_FOLDER, { intermediates: true });
          console.log("📁 Audio folder created:", AUDIO_FOLDER);
        } else {
          console.log("📁 Audio folder exists:", AUDIO_FOLDER);
        }
      } catch (err) {
        console.error("❌ Error ensuring audio folder:", err);
      }
    })();

    const socket = new WebSocket('ws://192.168.0.199:8000/ws'); // update your backend IP if needed

    socket.onopen = () => {
      console.log("WS connected");
    };

    socket.onmessage = async (event) => {
      // try parse json
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch (e) {
        // fallback plain text
        payload = { text: event.data, emotion: "neutral" };
      }

      const { text, emotion, audio_b64, audio_name, audio_index } = payload;

      // append textual message
      setMessages(prev => [...prev, { sender: 'Buddy', text, emotion }]);

      // handle audio if present
      if (audio_b64 && audio_name != null && typeof audio_index !== 'undefined') {
        const filename = `msg_${audio_index}.mp3`;
        const path = AUDIO_FOLDER + filename;

        try {
          // write base64 audio
          await FileSystem.writeAsStringAsync(path, audio_b64, { encoding: FileSystem.EncodingType.Base64 });
          console.log("✅ Audio file written:", path);

          // check file info
          const info = await FileSystem.getInfoAsync(path);
          console.log("📄 Audio file info:", info);

          // optional: overwrite latest.mp3
          const latestPath = AUDIO_FOLDER + "latest.mp3";
          try {
            await FileSystem.copyAsync({ from: path, to: latestPath });
          } catch (e) {
            await FileSystem.writeAsStringAsync(latestPath, audio_b64, { encoding: FileSystem.EncodingType.Base64 });
          }

          // play the audio
          await playSound(path);
        } catch (err) {
          console.error("❌ Error handling audio file:", err);
        }
      }
    };

    socket.onerror = (err) => {
      console.warn("WS error", err);
    };

    socket.onclose = () => {
      console.log("WS closed");
    };

    setWs(socket);
    return () => {
      if (soundRef.current) {
        soundRef.current.unloadAsync();
      }
      socket.close();
    };
  }, []);

  const playSound = async (uri) => {
    try {
      console.log("▶️ Attempting to play sound at:", uri);
      if (soundRef.current) {
        await soundRef.current.unloadAsync();
        soundRef.current = null;
      }
      const { sound } = await Audio.Sound.createAsync(
        { uri: uri },
        { shouldPlay: true }
      );
      soundRef.current = sound;
      console.log("✅ Audio playback started");
    } catch (e) {
      console.error("❌ playSound error:", e);
    }
  };

  const sendMessage = () => {
    if (ws && input.trim() !== '') {
      // send JSON to backend
      ws.send(JSON.stringify({ text: input, speaker: "user" }));
      setMessages(prev => [...prev, { sender: 'You', text: input }]);
      setInput('');
    }
  };

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.container}>
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        >
          <ScrollView
            style={styles.messagesContainer}
            ref={scrollViewRef}
            onContentSizeChange={() => scrollViewRef.current.scrollToEnd({ animated: true })}
          >
            {messages.map((msg, index) => (
              <MessageBubble
                key={index}
                text={msg.text}
                sender={msg.sender}
                emotion={msg.emotion}
              />
            ))}
          </ScrollView>
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              value={input}
              onChangeText={setInput}
              placeholder="Type your message"
            />
            <TouchableOpacity style={styles.sendButton} onPress={sendMessage}>
              <Text style={{ color: 'white', fontWeight: 'bold' }}>Send</Text>
            </TouchableOpacity>
          </View>
        </KeyboardAvoidingView>
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f2f2f2' },
  messagesContainer: { flex: 1, paddingHorizontal: 10, marginBottom: 10 },
  inputContainer: { flexDirection: 'row', paddingHorizontal: 10, paddingVertical: 5, alignItems: 'center' },
  input: { flex: 1, borderWidth: 1, borderColor: '#ccc', borderRadius: 20, paddingHorizontal: 15, paddingVertical: 10, marginRight: 10, backgroundColor: 'white' },
  sendButton: { backgroundColor: '#007AFF', paddingHorizontal: 15, paddingVertical: 10, borderRadius: 20 }
});
