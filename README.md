# Dynamic Wallpaper Creator

KDE Plasma supports dynamic wallpapers that switch between a light and a dark image to match your color scheme, but it has no built-in way to make one from your own images. This web app does that for you.

Everything happens in your browser. Your images are never uploaded.

## Usage

1. Enter a name for the wallpaper, and optionally an author.
2. Drop an image on the **Light** side and another on the **Dark** side, or click each side to choose a file.
3. Click **Download wallpaper** to save a `.zip` file.
4. Extract it into your wallpapers folder:

   ```sh
   unzip My-Wallpaper.zip -d ~/.local/share/wallpapers/
   ```

5. Open **System Settings → Wallpaper** (or right-click the desktop and choose **Desktop and Wallpaper**) and pick your new wallpaper.

Plasma shows the light image when you use a light color scheme and the dark image when you use a dark one.
