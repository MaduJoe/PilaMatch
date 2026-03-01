import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.pilamatch.app',
  appName: 'PilaMatch',
  webDir: 'out',
  server: {
    // In development, point to local Next.js server
    // url: 'http://localhost:3000',
    androidScheme: 'https',
  },
  plugins: {
    PushNotifications: {
      presentationOptions: ['badge', 'sound', 'alert'],
    },
  },
};

export default config;
