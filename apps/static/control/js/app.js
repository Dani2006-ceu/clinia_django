/* Sonrisa Perfecta - comportamiento de la interfaz (sin librerías externas) */
document.addEventListener("DOMContentLoaded", () => {
  // Menú lateral en pantallas pequeñas
  const btnMenu = document.getElementById("btnMenu");
  const sidebar = document.getElementById("sidebar");
  if (btnMenu && sidebar) {
    btnMenu.addEventListener("click", () => sidebar.classList.toggle("abierto"));
    document.addEventListener("click", (e) => {
      if (sidebar.classList.contains("abierto") && !sidebar.contains(e.target) && e.target !== btnMenu) {
        sidebar.classList.remove("abierto");
      }
    });
  }

  // Cerrar alertas (y ocultar las de éxito tras 5 segundos)
  document.querySelectorAll(".alerta").forEach((a) => {
    a.querySelector(".cerrar")?.addEventListener("click", () => a.remove());
    if (a.classList.contains("alerta-success")) setTimeout(() => a.remove(), 5000);
  });

  // Confirmación antes de eliminar
  document.querySelectorAll("form[data-confirmar]").forEach((f) => {
    f.addEventListener("submit", (e) => {
      if (!confirm(f.dataset.confirmar)) e.preventDefault();
    });
  });

  // Mostrar / ocultar contraseña
  document.querySelectorAll(".ver-clave").forEach((b) => {
    b.addEventListener("click", () => {
      const input = document.getElementById(b.dataset.objetivo);
      const oculto = input.type === "password";
      input.type = oculto ? "text" : "password";
      if (b.classList.contains("ojo")) {
        b.classList.toggle("activo", oculto);
        b.setAttribute("aria-label", oculto ? "Ocultar contraseña" : "Mostrar contraseña");
      } else {
        b.textContent = oculto ? "Ocultar" : "Ver";
      }
    });
  });

  // DNI: solo dígitos
  document.querySelectorAll('input[name="dni"]').forEach((i) => {
    i.addEventListener("input", () => { i.value = i.value.replace(/\D/g, "").slice(0, 8); });
  });

  // Validación en el navegador antes de enviar (el servidor vuelve a validar todo)
  document.querySelectorAll("form[data-validar]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      let primero = null;
      form.querySelectorAll(".error.js").forEach((x) => x.remove());
      form.querySelectorAll("input, select, textarea").forEach((campo) => {
        if (campo.type === "hidden") return;
        let mensaje = "";
        if (campo.required && !campo.value.trim()) mensaje = "Este campo es obligatorio.";
        else if (campo.value && !campo.checkValidity()) mensaje = campo.validationMessage;
        const contenedor = campo.closest(".campo");
        contenedor?.classList.toggle("con-error", !!mensaje);
        if (mensaje && contenedor) {
          const span = document.createElement("span");
          span.className = "error js";
          span.textContent = mensaje;
          contenedor.appendChild(span);
          primero = primero || campo;
        }
      });
      if (primero) { e.preventDefault(); primero.focus(); }
    });
  });

  // Botón de impresión (Guardar como PDF desde el navegador)
  document.querySelectorAll("[data-imprimir]").forEach((b) => b.addEventListener("click", () => window.print()));
});
