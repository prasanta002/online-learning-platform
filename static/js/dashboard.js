document.addEventListener("DOMContentLoaded", function () {

    const progressBars = document.querySelectorAll(".progress-bar");

    progressBars.forEach(function (bar) {

        const progress = bar.getAttribute("data-progress");

        bar.style.width = progress + "%";

    });

});