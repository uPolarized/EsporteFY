document.addEventListener("DOMContentLoaded", () => {
  const starGroups = document.querySelectorAll(".star-rating");

  starGroups.forEach(group => {
    const stars = group.querySelectorAll("input");

    stars.forEach(input => {
      input.addEventListener("change", e => {
        const allLabels = group.querySelectorAll("label");
        allLabels.forEach(lbl => lbl.classList.remove("selected"));

        const val = parseInt(e.target.value);
        for (let i = 0; i < val; i++) {
          allLabels[i].classList.add("selected");
        }
      });
    });
  });
});
