index = """
<div class="fast-microservices-topbar">
    <div class="fast-microservices-logo">fastmicroservices</div>
    
        <nav class="fast-microservices-nav-buttons">
            {% for page in pages %}
                <a class="fast-microservices-nav-btn"
                    hx-get="/page/{{ page.name }}"
                    hx-target="#main-content"
                    data-page="{{ page.name }}"
                    onclick="setActiveButton(this)">
                    {{ page.title }}
                </a>
            {% endfor %}
        </nav>
</div>

<div id="main-content"
   class="fast-microservices-main-content"
   hx-get="/page/dashboard"
   hx-trigger="load"
   hx-swap="innerHTML">
<div class="fast-microservices-welcome">
  <div>
    <h1 class="fast-microservices-welcome-title">Welcome to FastMicroservices</h1>
    <p class="fast-microservices-welcome-subtitle">
      Select a service from the navigation above to get started.
    </p>
  </div>
</div>
</div>

<script>
    function setActiveButton(clickedButton) {
      document.querySelectorAll('.fast-microservices-nav-btn')
        .forEach(btn => btn.classList.remove('fast-microservices-active'));
      clickedButton.classList.add('fast-microservices-active');
    }
</script>
"""

microservice_iframe = """
<div class="page-content" style="height: calc(100vh - 60px); padding: 0; margin: 0;">
    <iframe src="{{ url }}"
            width="100%"
            height="100%"
            frameborder="0"
            class="microservice-frame"
            style="display: block;">
    </iframe>
</div>
"""

fastmicroservices_css = """
/* Reset & base */
* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
  background: #1a1a2e;
  color: #fff;
  height: 100vh;
  overflow: hidden;
}

/* Top bar */
.fast-microservices-topbar {
  height: 60px;
  background: #2d2d44;
  border-bottom: 1px solid #444;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  gap: 2rem;
}

.fast-microservices-logo {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
}

/* Nav buttons */
.fast-microservices-nav-buttons {
  display: flex;
  gap: 0.5rem;
}

.fast-microservices-nav-btn {
  padding: 0.5rem 1rem;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 6px;
  color: #fff;
  text-decoration: none;
  font-size: 0.9rem;
  transition: background .2s ease, color .2s ease, border-color .2s ease, transform .2s ease;
  cursor: pointer;
}

.fast-microservices-nav-btn:hover {
  background: rgba(255,255,255,0.2);
  color: #fff;
}

.fast-microservices-nav-btn.fast-microservices-active {
  background: #4f46e5;
  border-color: #4f46e5;
}

/* Main content */
.fast-microservices-main-content {
  height: calc(100vh - 60px);
  width: 100%;
}

.fast-microservices-main-content iframe {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
}

/* Welcome state */
.fast-microservices-welcome {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

.fast-microservices-welcome-title {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.fast-microservices-welcome-subtitle {
  opacity: 0.7;
}
"""