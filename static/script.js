document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("file-input");
    const previewImage = document.getElementById("preview-image");
    const uploadButton = document.getElementById("upload-btn");
    const dragMsg = document.getElementById("drag-msg");
    const dragSubMsg = document.getElementById("drag-sub-msg");
    const resultMessage = document.getElementById("result-message");
    const loadingIndicator = document.getElementById("loading");
    const tableHeader = document.getElementById("table-header");
    const tableBody = document.getElementById("table-body");
    const dropZone = document.getElementById("drop-zone");
    const imageContainer = document.getElementById("image-container");
    const deleteBtn = document.getElementById("delete-image");
    const deviceSelect = document.getElementById("device-select");
    const label = document.getElementById("device-select-label");

    let selectedDevice = "";
    let selectedHdl = "";
    let uploadedImageFile = null; // Track uploaded file

    // Clicking dropzone opens file explorer
    dropZone.addEventListener("click", () => {
        fileInput.click();
    });

    // File input change
    fileInput.addEventListener("change", function () {
        if (this.files.length > 0) {
            handleFile(this.files[0]);
        }
    });

    // Drag-over and drop handling
    dropZone.addEventListener("dragover", function (e) {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", function () {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", function (e) {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    // Handle image preview
    function handleFile(file) {
        if (!file || !file.type.startsWith("image/")) {
            alert("Please upload a valid image file.");
            return;
        }

        if (file.size > 4 * 1024 * 1024) {
            alert("Image must be smaller than 4MB.");
            return;
        }

        uploadedImageFile = file; // store globally

        const reader = new FileReader();
        reader.onload = function (e) {
            previewImage.src = e.target.result;
            imageContainer.style.display = "block";
            dragMsg.style.display = "none";
            dragSubMsg.style.display = "none";
        };
        reader.readAsDataURL(file);
    }

    // Delete image
    deleteBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.value = "";
        uploadedImageFile = null;
        imageContainer.style.display = "none";
        previewImage.src = "";
        dragMsg.style.display = "block";
        dragSubMsg.style.display = "block";
        resultMessage.innerHTML = "Analysis result will be displayed here.";
        const tableBody = document.getElementById("data-table");
        const row = `<tr><td colspan="3">Upload an image to see results</td></tr>`;
        tableBody.innerHTML = row;
    });

    // Update analysis table
    function updateTable(data) {
        const tableBody = document.getElementById("data-table");
        tableBody.innerHTML = "";
        console.log(data);
        data.forEach((item) => {
            const row = `<tr class="table-row">
                <td>${item["Tree No"]}</td>
                <td>${item["Powerline No"]}</td>
                <td>${item["Result"]}</td>
            </tr>`;
            tableBody.innerHTML += row;
        });
    }

    // Handle device dropdown
    deviceSelect.addEventListener("change", function () {
        const selectedOption = deviceSelect.options[deviceSelect.selectedIndex];
        selectedDevice = selectedOption.value;
        selectedHdl = selectedOption.dataset.hdl || "";
        deviceSelect.disabled = false;
        label.style.color = "black";
    });

    // Upload button click
    uploadButton.addEventListener("click", function () {
        if (!uploadedImageFile) {
            alert("Please select an image first!");
            return;
        }

        const latitude = document.getElementById("latitude").value;
        const longitude = document.getElementById("longitude").value;

        if (!latitude || !longitude) {
            alert("Please enter latitude and longitude!");
            return;
        }

        if (!selectedDevice || !selectedHdl) {
            alert("Please select a device!");
            return;
        }

        loadingIndicator.style.display = "block";
        resultMessage.innerHTML = "Analyzing...";

        const formData = new FormData();
        formData.append("image", uploadedImageFile);
        formData.append("latitude", latitude);
        formData.append("longitude", longitude);
        formData.append("alias", selectedDevice);
        formData.append("hdl", selectedHdl);

        fetch("/analyze", {
            method: "POST",
            body: formData,
        })
            .then((response) => response.json())
            .then((data) => {
                loadingIndicator.style.display = "none";
                resultMessage.innerHTML = data.message;
                updateTable(data.tabulation);
            })
            .catch((error) => {
                loadingIndicator.style.display = "none";
                resultMessage.innerHTML = "❌ Error processing image.";
                console.error("Error:", error);
            });
    });

    // Load devices based on lat/lon
    document.getElementById("load-devices-btn").addEventListener("click", function () {
        const longitude = document.getElementById("longitude").value;
        const latitude = document.getElementById("latitude").value;

        if (!latitude || !longitude) {
            alert("Please enter latitude and longitude first!");
            return;
        }

        fetch("/get_devices", {
            method: "POST",
            body: new URLSearchParams({
                latitude: latitude,
                longitude: longitude,
            }),
        })
            .then((response) => response.json())
            .then((devices) => {
                const deviceSelect = document.getElementById("device-select");
                const label = document.getElementById("device-select-label");
                deviceSelect.innerHTML = '<option value="">Please select</option>';
                devices.forEach((device) => {
                    const option = document.createElement("option");
                    option.value = device.alias;
                    option.dataset.hdl = device.Hdl;
                    option.textContent = device.alias;
                    deviceSelect.appendChild(option);
                    deviceSelect.disabled = false;
                    label.style.color = "black";
                });
            })
            .catch((error) => console.error("Error fetching devices:", error));
    });
});
