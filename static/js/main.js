// "use strict";
//
// var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();
//
// function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }
//
// function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }
//
// var DragAndDrop = function () {
//   function DragAndDrop(el) {
//     _classCallCheck(this, DragAndDrop);
//
//     this.el = el;
//   }
//
//   _createClass(DragAndDrop, [{
//     key: "render",
//     value: function render() {
//       this.el.innerHTML = "\n      <div id=\"drop-area\">\n        <form enctype=\"multipart/form-data\" class=\"my-form\" id=\"uploadForm\">\n          <p>Drag and drop a video clip or load the <a href=\"/?action=load_sample\">sample video</a>.</p>\n          <input type=\"file\" id=\"fileElem\" accept=\"file_extension\"  name=\"upload\">\n          <label class=\"button\" for=\"fileElem\">Select a file</label>\n        </form>\n        <progress id=\"progress-bar\" max=\"100\" value=\"10\"></progress>\n        <div id=\"gallery\"></div>\n      </div>\n    ";
//     }
//   }, {
//     key: "init",
//     value: function init() {
//       var dropArea = this.el.querySelector("#drop-area");
//       var progressBar = this.el.querySelector("#progress-bar");
//       var fileElem = this.el.querySelector("#fileElem");
//       var gallery = this.el.querySelector("#gallery");
//       var uploadProgress = [];
//
//       function preventDefaults(e) {
//         e.preventDefault();
//         e.stopPropagation();
//       }
//
//       function highlight() {
//         dropArea.classList.add("highlight");
//       }
//
//       function unHighlight() {
//         dropArea.classList.remove("active");
//       }
//
//       dropArea.addEventListener("drop", handleDrop, false);
//       fileElem.addEventListener("change", handleFiles.bind(fileElem.files));
//
//       ["dragenter", "dragover", "dragleave", "drop"].forEach(function (eventName) {
//         dropArea.addEventListener(eventName, preventDefaults, false);
//       });
//
//       ["dragenter", "dragover"].forEach(function (eventName) {
//         dropArea.addEventListener(eventName, highlight, false);
//       });
//
//       ["dragleave", "drop"].forEach(function (eventName) {
//         dropArea.addEventListener(eventName, unHighlight, false);
//       });
//
//       function handleDrop(e) {
//         var dt = e.dataTransfer;
//         var files = dt.files;
//         files = [].concat(_toConsumableArray(files));
//         initializeProgress(files.length);
//         files.forEach(uploadFile);
//         files.forEach(previewFile);
//       }
//
//       function initializeProgress(numFiles) {
//         progressBar.value = 0;
//         uploadProgress = [];
//         for (var i = numFiles; i > 0; i--) {
//           uploadProgress.push(0);
//         }
//       }
//
//       function updateProgress(fileNumber, percent) {
//         uploadProgress[fileNumber] = percent;
//         var total = uploadProgress.reduce(function (tot, curr) {
//           return tot + curr;
//         }, 0) / uploadProgress.length;
//         console.debug("update", fileNumber, percent, total);
//         progressBar.value = total;
//       }
//
//       function handleFiles(files) {
//         files = [].concat(_toConsumableArray(files.target.files));
//         initializeProgress(files.length);
//         files.forEach(uploadFile);
//         files.forEach(previewFile);
//       }
//
//       function previewFile(file) {
//         var reader = new FileReader();
//         reader.readAsDataURL(file);
//         reader.onloadend = function () {
//           if (file.type === "image/jpeg" || file.type === "image/png" || file.type === "image/gif") {
//             var img = document.createElement("img");
//             img.src = reader.result;
//             gallery.appendChild(img);
//           } else {
//             var doc = document.createElement("img");
//             doc.src = "https://raw.githubusercontent.com/heysafronov/drag-and-drop/master/src/assets/img/document.png";
//             gallery.appendChild(doc);
//           }
//         };
//       }
//
//       function uploadFile(file, i) {
//         var url = "/upload";
//         var formData = new FormData();
//         formData.append("file", file);
//         var frameFrequency = $("#select-speed").find(":selected").text();
//         formData.append("frequency", frameFrequency);
//         // $("#uploadForm").submit();
//         fetch(url, {
//           method: "POST",
//           body: formData
//         }).then(function () {
//           updateProgress(i, 100);
//           window.location.href = "/";
//           console.log("redirecting");
//         }).catch(function () {
//           console.error("change the URL /uploadFile function/ to work with your back-end");
//         });
//       }
//     }
//   }, {
//     key: "run",
//     value: function run() {
//       this.render();
//       this.init();
//     }
//   }]);
//
//   return DragAndDrop;
// }();
//
// var element = document.querySelector("#drag-and-drop");
// var dragAndDrop = new DragAndDrop(element);
// dragAndDrop.run();
//

// var dropzone = new Dropzone('#demo-upload', {
//   url: '/upload',
//   previewTemplate: document.querySelector('#preview-template').innerHTML,
//   parallelUploads: 1,
//   thumbnailHeight: 120,
//   thumbnailWidth: 120,
//   maxFilesize: 10,
//   acceptedFiles: ".mp4,.mkv,.avi",
//   filesizeBase: 1000,
//   thumbnail: function(file, dataUrl) {
//     if (file.previewElement) {
//       file.previewElement.classList.remove("dz-file-preview");
//       var images = file.previewElement.querySelectorAll("[data-dz-thumbnail]");
//       for (var i = 0; i < images.length; i++) {
//         var thumbnailElement = images[i];
//         thumbnailElement.alt = file.name;
//         thumbnailElement.src = dataUrl;
//       }
//       setTimeout(function() { file.previewElement.classList.add("dz-image-preview"); }, 1);
//     }
//   }
//
// });
//
//
// // Now fake the file upload, since GitHub does not handle file uploads
// // and returns a 404
//
// var minSteps = 6,
//     maxSteps = 60,
//     timeBetweenSteps = 100,
//     bytesPerStep = 100000;
//
// dropzone.uploadFiles = function(files) {
//   var self = this;
//
//   for (var i = 0; i < files.length; i++) {
//
//     var file = files[i];
//     totalSteps = Math.round(Math.min(maxSteps, Math.max(minSteps, file.size / bytesPerStep)));
//
//     for (var step = 0; step < totalSteps; step++) {
//       var duration = timeBetweenSteps * (step + 1);
//       setTimeout(function(file, totalSteps, step) {
//         return function() {
//           file.upload = {
//             progress: 100 * (step + 1) / totalSteps,
//             total: file.size,
//             bytesSent: (step + 1) * file.size / totalSteps
//           };
//
//           self.emit('uploadprogress', file, file.upload.progress, file.upload.bytesSent);
//           if (file.upload.progress == 100) {
//             file.status = Dropzone.SUCCESS;
//             self.emit("success", file, 'success', null);
//             self.emit("complete", file);
//             self.processQueue();
//             //document.getElementsByClassName("dz-success-mark").style.opacity = "1";
//           }
//         };
//       }(file, totalSteps, step), duration);
//     }
//   }
// }


// // Get the template HTML and remove it from the doumenthe template HTML and remove it from the doument
// var previewNode = document.querySelector("#template");
// previewNode.id = "";
// var previewTemplate = previewNode.parentNode.innerHTML;
// previewNode.parentNode.removeChild(previewNode);
//
// var myDropzone = new Dropzone(document.body, { // Make the whole body a dropzone
//   url: "/target-url", // Set the url
//   thumbnailWidth: 80,
//   thumbnailHeight: 80,
//   parallelUploads: 20,
//   previewTemplate: previewTemplate,
//   autoQueue: false, // Make sure the files aren't queued until manually added
//   previewsContainer: "#previews", // Define the container to display the previews
//   clickable: "#upload-form" // Define the element that should be used as click trigger to select files.
// });
//
// myDropzone.on("addedfile", function(file) {
//   // Hookup the start button
//   file.previewElement.querySelector(".start").onclick = function() { myDropzone.enqueueFile(file); };
// });
//
// // Update the total progress bar
// myDropzone.on("totaluploadprogress", function(progress) {
//   document.querySelector("#total-progress .progress-bar").style.width = progress + "%";
// });
//
// myDropzone.on("sending", function(file) {
//   // Show the total progress bar when upload starts
//   document.querySelector("#total-progress").style.opacity = "1";
//   // And disable the start button
//   file.previewElement.querySelector(".start").setAttribute("disabled", "disabled");
// });
//
// // Hide the total progress bar when nothing's uploading anymore
// myDropzone.on("queuecomplete", function(progress) {
//   document.querySelector("#total-progress").style.opacity = "0";
// });
//
// // Setup the buttons for all transfers
// // The "add files" button doesn't need to be setup because the config
// // `clickable` has already been specified.
// document.querySelector("#actions .start").onclick = function() {
//   myDropzone.enqueueFiles(myDropzone.getFilesWithStatus(Dropzone.ADDED));
// };
// document.querySelector("#actions .cancel").onclick = function() {
//   myDropzone.removeAllFiles(true);
// };