// Sends the device's screen as JPEG images, one per request.
//
// Needs Android 14 (API 34) or newer, for the hidden mirroring call below.
// Runs with shell permissions, started over adb the way scrcpy's server is:
//
//   adb push jpeg-server.jar /data/local/tmp/
//   adb forward tcp:PORT localabstract:jpeg_server
//   adb shell CLASSPATH=/data/local/tmp/jpeg-server.jar app_process / JpegServer WIDTH HEIGHT QUALITY
//
// It mirrors the main display onto an ImageReader at WIDTH x HEIGHT (with
// DisplayManager's hidden createVirtualDisplay, as scrcpy does), and
// encodes the newest image only when a client asks for one, so a frame is
// never older than the time it takes to encode and send it.
//
// Protocol, all big-endian. On connect the server sends a header:
//   4 bytes "JPGS", int32 version (1), int32 width, int32 height,
//   int32 display width, int32 display height (the real display, so the
//   client can tell when its shape doesn't match the frames)
// Then the client sends 1-byte requests:
//   'p' (ping): answered with int64 System.nanoTime(), to line up clocks.
//   'f' (frame): answered with
//     int64 capture time (ns, System.nanoTime clock), int64 send time (ns),
//     int32 status: > 0, the length of the JPEG that follows;
//                   0, no new image since the last frame sent (the screen
//                      hasn't changed); the capture time is the last one's;
//                  -1, the display is off.
// The server serves one client at a time, and waits for the next when one
// disconnects. Anything else from the client closes the connection.

import android.graphics.Bitmap;
import android.graphics.PixelFormat;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.net.LocalServerSocket;
import android.net.LocalSocket;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.Looper;
import android.view.Display;
import android.view.Surface;

import java.io.BufferedOutputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.ByteBuffer;

public final class JpegServer {
    private static final String SOCKET_NAME = "jpeg_server";
    private static final int VERSION = 1;
    private static final int NO_NEW_IMAGE = 0;
    private static final int DISPLAY_OFF = -1;

    private final int width;
    private final int height;
    private final int quality;
    private final ImageReader reader;
    private final Object displayManager;  // DisplayManagerGlobal
    private final ByteArrayOutputStream jpeg = new ByteArrayOutputStream(256 * 1024);
    private Bitmap bitmap;
    private ByteBuffer packed;  // rows without padding, when the image has some
    private long lastCapture;

    private JpegServer(int width, int height, int quality, ImageReader reader) throws Exception {
        this.width = width;
        this.height = height;
        this.quality = quality;
        this.reader = reader;
        Class<?> global = Class.forName("android.hardware.display.DisplayManagerGlobal");
        displayManager = global.getDeclaredMethod("getInstance").invoke(null);
    }

    public static void main(String[] args) throws Exception {
        int width = Integer.parseInt(args[0]);
        int height = Integer.parseInt(args[1]);
        int quality = Integer.parseInt(args[2]);

        // Encoding runs on this thread, and the game competes for the CPU:
        // ask for display priority. It's only a request.
        try {
            android.os.Process.setThreadPriority(android.os.Process.THREAD_PRIORITY_URGENT_DISPLAY);
        } catch (RuntimeException e) {
            System.out.println("couldn't raise priority: " + e);
        }
        if (Looper.getMainLooper() == null) {
            Looper.prepareMainLooper();
        }
        HandlerThread images = new HandlerThread("images");
        images.start();
        // Two buffers: one being read here while the display fills the other.
        ImageReader reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2);
        // Images are pulled when asked for, but the reader needs a looper.
        reader.setOnImageAvailableListener(r -> { }, new Handler(images.getLooper()));
        VirtualDisplay mirror = mirror(width, height, reader.getSurface());

        JpegServer server = new JpegServer(width, height, quality, reader);
        System.out.println("serving " + width + "x" + height + " at quality " + quality
                + " on localabstract:" + SOCKET_NAME);
        try (LocalServerSocket socket = new LocalServerSocket(SOCKET_NAME)) {
            while (true) {
                try (LocalSocket client = socket.accept()) {
                    server.serve(client);
                } catch (IOException e) {
                    System.out.println("client gone: " + e);
                }
            }
        } finally {
            mirror.release();
            reader.close();
            images.quitSafely();
        }
    }

    private static VirtualDisplay mirror(int width, int height, Surface surface) throws Exception {
        Method create = android.hardware.display.DisplayManager.class.getMethod(
                "createVirtualDisplay", String.class, int.class, int.class, int.class, Surface.class);
        return (VirtualDisplay) create.invoke(null, "jpeg_server", width, height, Display.DEFAULT_DISPLAY, surface);
    }

    private void serve(LocalSocket client) throws Exception {
        DataInputStream in = new DataInputStream(client.getInputStream());
        DataOutputStream out = new DataOutputStream(new BufferedOutputStream(client.getOutputStream(), 256 * 1024));
        Object info = displayInfo();
        out.writeBytes("JPGS");
        out.writeInt(VERSION);
        out.writeInt(width);
        out.writeInt(height);
        out.writeInt(intField(info, "logicalWidth"));
        out.writeInt(intField(info, "logicalHeight"));
        out.flush();
        // Only images captured from now on count as new for this client.
        lastCapture = 0;
        while (true) {
            int request;
            try {
                request = in.readUnsignedByte();
            } catch (EOFException e) {
                return;
            }
            if (request == 'p') {
                out.writeLong(System.nanoTime());
            } else if (request == 'f') {
                sendFrame(out);
            } else {
                System.out.println("unknown request " + request + ", closing");
                return;
            }
            out.flush();
        }
    }

    private void sendFrame(DataOutputStream out) throws Exception {
        Image image = reader.acquireLatestImage();
        if (image == null) {
            int status = displayOn() ? NO_NEW_IMAGE : DISPLAY_OFF;
            out.writeLong(lastCapture);
            out.writeLong(System.nanoTime());
            out.writeInt(status);
            return;
        }
        long captured;
        try {
            captured = image.getTimestamp();
            copyToBitmap(image);
        } finally {
            image.close();
        }
        jpeg.reset();
        bitmap.compress(Bitmap.CompressFormat.JPEG, quality, jpeg);
        lastCapture = captured;
        out.writeLong(captured);
        out.writeLong(System.nanoTime());
        out.writeInt(jpeg.size());
        jpeg.writeTo(out);
    }

    /** The image's pixels into the bitmap, dropping any padding at the
     *  ends of rows. */
    private void copyToBitmap(Image image) {
        if (bitmap == null) {
            bitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888);
        }
        Image.Plane plane = image.getPlanes()[0];
        ByteBuffer pixels = plane.getBuffer();
        int rowBytes = width * 4;
        int stride = plane.getRowStride();
        if (stride == rowBytes) {
            pixels.rewind();
            bitmap.copyPixelsFromBuffer(pixels);
            return;
        }
        if (packed == null) {
            packed = ByteBuffer.allocateDirect(rowBytes * height);
            System.out.println("rows are padded to " + stride + " bytes, repacking each frame");
        }
        packed.clear();
        ByteBuffer row = pixels.duplicate();
        for (int y = 0; y < height; y++) {
            row.limit(y * stride + rowBytes).position(y * stride);
            packed.put(row);
        }
        packed.flip();
        bitmap.copyPixelsFromBuffer(packed);
    }

    private Object displayInfo() throws Exception {
        Method get = displayManager.getClass().getMethod("getDisplayInfo", int.class);
        return get.invoke(displayManager, Display.DEFAULT_DISPLAY);
    }

    private boolean displayOn() throws Exception {
        int state = intField(displayInfo(), "state");
        return state == Display.STATE_ON || state == Display.STATE_VR;
    }

    private static int intField(Object object, String name) throws Exception {
        Field field = object.getClass().getField(name);
        return field.getInt(object);
    }
}
