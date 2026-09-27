import { strToU8, zipSync } from "fflate";
import "./style.css";

const images = { light: null, dark: null };

const form = document.getElementById("form");
const nameInput = document.getElementById("name");
const authorInput = document.getElementById("author");
const errorBox = document.getElementById("error");
const zipName = document.getElementById("zip-name");

function slugify(name) {
  return name.replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^[-.]+|[-.]+$/g, "") || "wallpaper";
}

function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = !message;
}

function extensionOf(file) {
  const match = /\.([A-Za-z0-9]+)$/.exec(file.name);
  if (match) return match[1].toLowerCase();
  return file.type.split("/")[1] || "png";
}

async function loadImage(variant, picker, file) {
  if (!file.type.startsWith("image/")) {
    showError(`“${file.name}” is not an image.`);
    return;
  }

  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
  } catch {
    showError(`Could not read “${file.name}”. Your browser may not support this format.`);
    return;
  }
  const { width, height } = bitmap;
  bitmap.close();

  const previous = images[variant];
  if (previous) URL.revokeObjectURL(previous.url);

  const url = URL.createObjectURL(file);
  images[variant] = { file, width, height, url };

  picker.classList.add("has-image");
  picker.querySelector(".drop").style.backgroundImage = `url("${url}")`;
  picker.querySelector(".info").textContent = `${file.name} · ${width}×${height}`;
  showError("");
}

for (const picker of document.querySelectorAll(".picker")) {
  const variant = picker.dataset.variant;
  const input = picker.querySelector("input[type=file]");

  input.addEventListener("change", () => {
    if (input.files[0]) loadImage(variant, picker, input.files[0]);
    input.value = "";
  });

  picker.addEventListener("dragover", (event) => {
    if (!event.dataTransfer.types.includes("Files")) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "copy";
    picker.classList.add("dragover");
  });

  picker.addEventListener("dragleave", (event) => {
    if (!picker.contains(event.relatedTarget)) picker.classList.remove("dragover");
  });

  picker.addEventListener("drop", (event) => {
    event.preventDefault();
    picker.classList.remove("dragover");
    const file = event.dataTransfer.files[0];
    if (file) loadImage(variant, picker, file);
  });
}

// Don't navigate away when a file is dropped outside the drop zones.
window.addEventListener("dragover", (event) => event.preventDefault());
window.addEventListener("drop", (event) => event.preventDefault());

nameInput.addEventListener("input", () => {
  zipName.textContent = slugify(nameInput.value.trim() || "My Wallpaper");
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const name = nameInput.value.trim();
  if (!name) {
    showError("Please enter a wallpaper name.");
    nameInput.focus();
    return;
  }
  if (!images.light || !images.dark) {
    showError("Please choose both a light and a dark image.");
    return;
  }
  showError("");

  const id = slugify(name);
  const metadata = { KPlugin: { Id: id, Name: name } };
  const author = authorInput.value.trim();
  if (author) metadata.KPlugin.Authors = [{ Name: author }];

  const imageEntry = async ({ file, width, height }) => ({
    [`${width}x${height}.${extensionOf(file)}`]: new Uint8Array(await file.arrayBuffer()),
  });

  // Images are already compressed, so store them as-is (level 0).
  const zipped = zipSync(
    {
      [id]: {
        "metadata.json": strToU8(JSON.stringify(metadata, null, 4) + "\n"),
        contents: {
          images: await imageEntry(images.light),
          images_dark: await imageEntry(images.dark),
        },
      },
    },
    { level: 0 },
  );
  const zip = new Blob([zipped], { type: "application/zip" });

  const link = document.createElement("a");
  link.href = URL.createObjectURL(zip);
  link.download = `${id}.zip`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
});
