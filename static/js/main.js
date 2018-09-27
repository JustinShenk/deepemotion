"use strict";

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var DragAndDrop = function () {
  function DragAndDrop(el) {
    _classCallCheck(this, DragAndDrop);

    this.el = el;
  }

  _createClass(DragAndDrop, [{
    key: "render",
    value: function render() {
      this.el.innerHTML = "\n      <div id=\"drop-area\">\n        <form enctype=\"multipart/form-data\" class=\"my-form\" id=\"uploadForm\">\n          <p>Drop a small (<5 MB) video clip or load the <a href=\"/?action=load_sample\">sample video</a>.</p>\n          <input type=\"file\" id=\"fileElem\" accept=\"file_extension\"  name=\"upload\">\n          <label class=\"button\" for=\"fileElem\">Select a file</label>\n        </form>\n        <progress id=\"progress-bar\" max=\"100\" value=\"10\"></progress>\n        <div id=\"gallery\"></div>\n      </div>\n    ";
    }
  }, {
    key: "init",
    value: function init() {
      var dropArea = this.el.querySelector("#drop-area");
      var progressBar = this.el.querySelector("#progress-bar");
      var fileElem = this.el.querySelector("#fileElem");
      var gallery = this.el.querySelector("#gallery");
      var uploadProgress = [];

      function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
      }

      function highlight() {
        dropArea.classList.add("highlight");
      }

      function unHighlight() {
        dropArea.classList.remove("active");
      }

      dropArea.addEventListener("drop", handleDrop, false);
      fileElem.addEventListener("change", handleFiles.bind(fileElem.files));

      ["dragenter", "dragover", "dragleave", "drop"].forEach(function (eventName) {
        dropArea.addEventListener(eventName, preventDefaults, false);
      });

      ["dragenter", "dragover"].forEach(function (eventName) {
        dropArea.addEventListener(eventName, highlight, false);
      });

      ["dragleave", "drop"].forEach(function (eventName) {
        dropArea.addEventListener(eventName, unHighlight, false);
      });

      function handleDrop(e) {
        var dt = e.dataTransfer;
        var files = dt.files;
        files = [].concat(_toConsumableArray(files));
        initializeProgress(files.length);
        files.forEach(uploadFile);
        files.forEach(previewFile);
      }

      function initializeProgress(numFiles) {
        progressBar.value = 0;
        uploadProgress = [];
        for (var i = numFiles; i > 0; i--) {
          uploadProgress.push(0);
        }
      }

      function updateProgress(fileNumber, percent) {
        uploadProgress[fileNumber] = percent;
        var total = uploadProgress.reduce(function (tot, curr) {
          return tot + curr;
        }, 0) / uploadProgress.length;
        console.debug("update", fileNumber, percent, total);
        progressBar.value = total;
      }

      function handleFiles(files) {
        files = [].concat(_toConsumableArray(files.target.files));
        initializeProgress(files.length);
        files.forEach(uploadFile);
        files.forEach(previewFile);
      }

      function previewFile(file) {
        var reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onloadend = function () {
          if (file.type === "image/jpeg" || file.type === "image/png" || file.type === "image/gif") {
            var img = document.createElement("img");
            img.src = reader.result;
            gallery.appendChild(img);
          } else {
            var doc = document.createElement("img");
            doc.src = "https://raw.githubusercontent.com/heysafronov/drag-and-drop/master/src/assets/img/document.png";
            gallery.appendChild(doc);
          }
        };
      }

      function uploadFile(file, i) {
        var url = "/upload";
        var formData = new FormData();
        formData.append("file", file);
        // $("#uploadForm").submit();
        fetch(url, {
          method: "POST",
          body: formData
        }).then(function () {
          updateProgress(i, 100);
          window.location.href = "/";
          console.log("redirecting");
        }).catch(function () {
          console.error("change the URL /uploadFile function/ to work with your back-end");
        });
      }
    }
  }, {
    key: "run",
    value: function run() {
      this.render();
      this.init();
    }
  }]);

  return DragAndDrop;
}();

var element = document.querySelector("#drag-and-drop");
var dragAndDrop = new DragAndDrop(element);
dragAndDrop.run();

