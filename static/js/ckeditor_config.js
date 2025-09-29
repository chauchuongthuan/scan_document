class MyUploadAdapter {
  constructor(loader) {
    this.loader = loader;
  }

  upload() {
    return this.loader.file.then(
      (file) =>
        new Promise((resolve, reject) => {
          this._initRequest();
          this._initListeners(resolve, reject, file);
          this._sendRequest(file);
        })
    );
  }

  abort() {
    if (this.xhr) {
      this.xhr.abort();
    }
  }

  _initRequest() {
    const xhr = (this.xhr = new XMLHttpRequest());
    xhr.open("POST", "/ckeditor5/image_upload/", true);
    xhr.setRequestHeader("X-CSRFToken", this.getCookie("csrftoken"));
    xhr.responseType = "json";
  }

  _initListeners(resolve, reject, file) {
    const xhr = this.xhr;
    const loader = this.loader;
    const genericErrorText = `Couldn't upload file: ${file.name}.`;

    xhr.addEventListener("error", () => reject(genericErrorText));
    xhr.addEventListener("abort", () => reject());
    xhr.addEventListener("load", () => {
      const response = xhr.response;
      if (!response || response.error) {
        return reject(
          response && response.error ? response.error.message : genericErrorText
        );
      }
      resolve({
        default: response.url,
      });
    });

    if (xhr.upload) {
      xhr.upload.addEventListener("progress", (evt) => {
        if (evt.lengthComputable) {
          loader.uploadTotal = evt.total;
          loader.uploaded = evt.loaded;
        }
      });
    }
  }

  _sendRequest(file) {
    const data = new FormData();
    data.append("upload", file);
    this.xhr.send(data);
  }

  getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
}

function MyCustomUploadAdapterPlugin(editor) {
  editor.plugins.get("FileRepository").createUploadAdapter = (loader) => {
    return new MyUploadAdapter(loader);
  };
}

// Khởi tạo CKEditor với custom upload adapter
document.addEventListener("DOMContentLoaded", (event) => {
  ClassicEditor.create(document.querySelector("#id_content"), {
    extraPlugins: [MyCustomUploadAdapterPlugin],
    // Thêm cấu hình cho image upload
    image: {
      upload: {
        types: ["jpeg", "png", "gif", "bmp", "webp", "tiff", "jpg"],
      },
      toolbar: [
        "imageStyle:inline",
        "imageStyle:block",
        "imageStyle:side",
        "|",
        "toggleImageCaption",
        "imageTextAlternative",
      ],
    },
    // Các cấu hình khác nếu cần
  })
    .then((editor) => {
      console.log("Editor was initialized", editor);
      window.editor = editor; // Lưu instance của editor vào biến global để sử dụng sau này
    })
    .catch((error) => {
      console.error("There was a problem initializing the editor.", error);
    });
  ClassicEditor.create(document.querySelector("#id_note"), {
    extraPlugins: [MyCustomUploadAdapterPlugin],
    // Thêm cấu hình cho image upload
    image: {
      upload: {
        types: ["jpeg", "png", "gif", "bmp", "webp", "tiff", "jpg"],
      },
      toolbar: [
        "imageStyle:inline",
        "imageStyle:block",
        "imageStyle:side",
        "|",
        "toggleImageCaption",
        "imageTextAlternative",
      ],
    },
    // Các cấu hình khác nếu cần
  })
    .then((editor) => {
      console.log("Editor was initialized", editor);
      window.editor = editor; // Lưu instance của editor vào biến global để sử dụng sau này
    })
    .catch((error) => {
      console.error("There was a problem initializing the editor.", error);
    });
});
