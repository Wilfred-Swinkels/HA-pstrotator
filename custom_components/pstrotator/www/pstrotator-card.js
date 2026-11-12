/**
 * PstRotator Card
 * Azimuthal-equidistant world map centered on the Home Assistant home
 * location. Click anywhere on the map to send that bearing to PstRotator,
 * or nudge the current bearing with the +/- buttons.
 */
(() => {
  const LAND_URL = "/pstrotator_files/land-110m.json";
  const DEG = Math.PI / 180;
  const EARTH_HALF_CIRCUMFERENCE_KM = 20015;

  let landDataPromise = null;
  function loadLandData() {
    if (!landDataPromise) {
      landDataPromise = fetch(LAND_URL)
        .then((r) => r.json())
        .catch(() => ({ features: [] }));
    }
    return landDataPromise;
  }

  function toRad(d) {
    return d * DEG;
  }

  function wrap360(a) {
    return ((a % 360) + 360) % 360;
  }

  // Azimuthal-equidistant projection centered on (lat0, lon0).
  // The returned angle `az` is the true great-circle bearing from the
  // center to (lat, lon) -- exactly the value PstRotator needs.
  function projectPoint(lat0, lon0, lat, lon, R) {
    const phi1 = toRad(lat0);
    const lambda0 = toRad(lon0);
    const phi = toRad(lat);
    const lambda = toRad(lon);
    const dLambda = lambda - lambda0;

    let cosc =
      Math.sin(phi1) * Math.sin(phi) +
      Math.cos(phi1) * Math.cos(phi) * Math.cos(dLambda);
    cosc = Math.max(-1, Math.min(1, cosc));
    const c = Math.acos(cosc);

    const theta = Math.atan2(
      Math.sin(dLambda) * Math.cos(phi),
      Math.cos(phi1) * Math.sin(phi) -
        Math.sin(phi1) * Math.cos(phi) * Math.cos(dLambda)
    );

    const r = (c / Math.PI) * R;
    const x = r * Math.sin(theta);
    const y = -r * Math.cos(theta);
    return { x, y, c, az: wrap360(theta / DEG) };
  }

  const SVG_NS = "http://www.w3.org/2000/svg";
  function svgEl(tag, attrs) {
    const el = document.createElementNS(SVG_NS, tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, v);
    }
    return el;
  }

  class PstRotatorCard extends HTMLElement {
    static getStubConfig() {
      return { entity: "", step: 5 };
    }

    setConfig(config) {
      if (!config || !config.entity) {
        throw new Error(
          "pstrotator-card: stel 'entity' in op de azimuth number-entiteit van PstRotator."
        );
      }
      this._config = {
        step: 5,
        title: "PstRotator",
        land_color: "#3f7a44",
        land_stroke: "#274d2b",
        ocean_from: "#2f7fb8",
        ocean_to: "#0b2b45",
        line_color: "#ff5a36",
        ...config,
      };
      this._built = false;
      this._dragging = false;
      this._dragAzimuth = null;
      this._lastSendTime = 0;
      this._render();
    }

    set hass(hass) {
      this._hass = hass;
      this._maybeRedrawBase();
      this._updateDynamic();
    }

    getCardSize() {
      return 7;
    }

    connectedCallback() {
      if (this._config && !this._built) this._render();
    }

    // Home location priority: explicit card config, then the attributes
    // PstRotator's number entity exposes (QTH locator / manual override
    // resolved by the integration), then Home Assistant's own home zone.
    _homeLocation() {
      const cfg = this._config;
      const attrs = this._hass?.states?.[cfg.entity]?.attributes || {};
      const lat =
        cfg.home_latitude != null
          ? cfg.home_latitude
          : attrs.home_latitude != null
          ? attrs.home_latitude
          : this._hass?.config?.latitude;
      const lon =
        cfg.home_longitude != null
          ? cfg.home_longitude
          : attrs.home_longitude != null
          ? attrs.home_longitude
          : this._hass?.config?.longitude;
      return { lat: Number(lat) || 0, lon: Number(lon) || 0 };
    }

    async _maybeRedrawBase() {
      if (!this._svg) return;
      const home = this._homeLocation();
      const prev = this._drawnHome;
      if (
        prev &&
        Math.abs(prev.lat - home.lat) < 1e-4 &&
        Math.abs(prev.lon - home.lon) < 1e-4
      ) {
        return;
      }
      await this._drawBase();
      this._updateDynamic();
    }

    _currentAzimuth() {
      const st = this._hass?.states?.[this._config.entity];
      const v = st ? parseFloat(st.state) : NaN;
      return Number.isFinite(v) ? v : 0;
    }

    async _render() {
      if (!this.shadowRoot) this.attachShadow({ mode: "open" });
      this._built = true;

      const cfg = this._config;
      this._R = 150;
      this._cx = 190;
      this._cy = 190;

      this.shadowRoot.innerHTML = `
        <style>
          ha-card {
            overflow: hidden;
            padding: 0;
          }
          .header {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            padding: 12px 16px 0 16px;
          }
          .title {
            font-size: 1.1rem;
            font-weight: 500;
            color: var(--primary-text-color);
          }
          .az-readout {
            font-size: 1.4rem;
            font-weight: 600;
            color: var(--primary-text-color);
            font-variant-numeric: tabular-nums;
          }
          .map-wrap {
            position: relative;
            padding: 4px 10px 10px 10px;
          }
          svg {
            display: block;
            width: 100%;
            height: auto;
            cursor: grab;
            user-select: none;
            touch-action: none;
          }
          svg.dragging {
            cursor: grabbing;
          }
          .nudge {
            position: absolute;
            bottom: 18px;
            border: none;
            border-radius: 20px;
            padding: 8px 16px;
            font-size: 1rem;
            font-weight: 600;
            color: #fff;
            background: var(--pstrotator-accent, #2f7fb8);
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
            cursor: pointer;
            transition: transform 0.08s ease-in-out;
          }
          .nudge:hover {
            transform: scale(1.06);
          }
          .nudge:active {
            transform: scale(0.96);
          }
          .nudge.minus {
            left: 20px;
          }
          .nudge.plus {
            right: 20px;
          }
          .hint {
            text-align: center;
            font-size: 0.78rem;
            color: var(--secondary-text-color);
            padding: 0 16px 10px 16px;
          }
        </style>
        <ha-card>
          <div class="header">
            <div class="title">${cfg.title ? cfg.title : ""}</div>
            <div class="az-readout" id="az-readout">--.-&deg;</div>
          </div>
          <div class="map-wrap">
            <svg id="svg" viewBox="0 0 380 380"></svg>
            <button class="nudge minus" id="minus">&minus;${cfg.step}&deg;</button>
            <button class="nudge plus" id="plus">+${cfg.step}&deg;</button>
          </div>
          <div class="hint">Klik op de kaart om de rotor die richting te laten draaien</div>
        </ha-card>
      `;

      this._svg = this.shadowRoot.getElementById("svg");
      this.shadowRoot
        .getElementById("minus")
        .addEventListener("click", () => this._nudge(-cfg.step));
      this.shadowRoot
        .getElementById("plus")
        .addEventListener("click", () => this._nudge(cfg.step));
      this._svg.addEventListener("pointerdown", (ev) => this._onPointerDown(ev));
      this._svg.addEventListener("pointermove", (ev) => this._onPointerMove(ev));
      this._svg.addEventListener("pointerup", (ev) => this._onPointerUp(ev));
      this._svg.addEventListener("pointercancel", (ev) => this._onPointerUp(ev));

      await this._drawBase();
      this._updateDynamic();
    }

    async _drawBase() {
      const cfg = this._config;
      const land = await loadLandData();
      const home = this._homeLocation();
      this._drawnHome = home;
      const { lat: lat0, lon: lon0 } = home;
      const R = this._R;
      const cx = this._cx;
      const cy = this._cy;
      const svg = this._svg;
      svg.innerHTML = "";

      const defs = svgEl("defs");
      const grad = svgEl("radialGradient", {
        id: "oceanGrad",
        cx: "50%",
        cy: "42%",
        r: "70%",
      });
      grad.appendChild(svgEl("stop", { offset: "0%", "stop-color": cfg.ocean_from }));
      grad.appendChild(svgEl("stop", { offset: "100%", "stop-color": cfg.ocean_to }));
      defs.appendChild(grad);

      const glow = svgEl("filter", { id: "needleGlow", x: "-50%", y: "-50%", width: "200%", height: "200%" });
      const blur = svgEl("feDropShadow", {
        dx: "0",
        dy: "0",
        stdDeviation: "2.2",
        "flood-color": cfg.line_color,
        "flood-opacity": "0.85",
      });
      glow.appendChild(blur);
      defs.appendChild(glow);

      const clip = svgEl("clipPath", { id: "oceanClip" });
      clip.appendChild(svgEl("circle", { cx, cy, r: R }));
      defs.appendChild(clip);

      svg.appendChild(defs);

      // Ocean background
      svg.appendChild(
        svgEl("circle", {
          cx,
          cy,
          r: R,
          fill: "url(#oceanGrad)",
          stroke: "var(--pstrotator-rim, #0a1f33)",
          "stroke-width": 2,
        })
      );

      // Distance rings
      const ringGroup = svgEl("g", { "clip-path": "url(#oceanClip)" });
      for (const km of [5000, 10000, 15000]) {
        const r = R * (km / EARTH_HALF_CIRCUMFERENCE_KM);
        ringGroup.appendChild(
          svgEl("circle", {
            cx,
            cy,
            r,
            fill: "none",
            stroke: "#ffffff",
            "stroke-opacity": 0.28,
            "stroke-width": 1,
            "stroke-dasharray": "3,4",
          })
        );
      }
      svg.appendChild(ringGroup);
      for (const km of [5000, 10000, 15000]) {
        const r = R * (km / EARTH_HALF_CIRCUMFERENCE_KM);
        if (r < 14) continue;
        const label = svgEl("text", {
          x: cx + 3,
          y: cy - r - 3,
          fill: "#ffffff",
          "fill-opacity": 0.55,
          "font-size": "8",
          "font-family": "sans-serif",
        });
        label.textContent = `${km / 1000}k km`;
        svg.appendChild(label);
      }

      // Land masses
      let d = "";
      for (const feature of land.features || []) {
        const geom = feature.geometry;
        if (!geom) continue;
        const polys = geom.type === "Polygon" ? [geom.coordinates] : geom.coordinates;
        for (const poly of polys) {
          for (const ring of poly) {
            let prev = null;
            for (const [lon, lat] of ring) {
              const p = projectPoint(lat0, lon0, lat, lon, R);
              const px = cx + p.x;
              const py = cy + p.y;
              if (prev === null) {
                d += `M${px.toFixed(1)},${py.toFixed(1)}`;
              } else {
                const jump = Math.hypot(px - prev[0], py - prev[1]);
                if (jump > R * 0.55) {
                  d += `M${px.toFixed(1)},${py.toFixed(1)}`;
                } else {
                  d += `L${px.toFixed(1)},${py.toFixed(1)}`;
                }
              }
              prev = [px, py];
            }
            d += "Z";
          }
        }
      }
      const landPath = svgEl("path", {
        d,
        fill: cfg.land_color,
        stroke: cfg.land_stroke,
        "stroke-width": 0.6,
        "stroke-linejoin": "round",
        "clip-path": "url(#oceanClip)",
        "fill-rule": "evenodd",
      });
      svg.appendChild(landPath);

      // Degree ticks + cardinal labels
      const tickGroup = svgEl("g");
      for (let deg = 0; deg < 360; deg += 10) {
        const rad = deg * DEG;
        const major = deg % 30 === 0;
        const rInner = R - (major ? 10 : 5);
        const x1 = cx + R * Math.sin(rad);
        const y1 = cy - R * Math.cos(rad);
        const x2 = cx + rInner * Math.sin(rad);
        const y2 = cy - rInner * Math.cos(rad);
        tickGroup.appendChild(
          svgEl("line", {
            x1,
            y1,
            x2,
            y2,
            stroke: "#ffffff",
            "stroke-opacity": major ? 0.85 : 0.4,
            "stroke-width": major ? 1.6 : 1,
          })
        );
        if (major) {
          const lr = R + 14;
          const lx = cx + lr * Math.sin(rad);
          const ly = cy - lr * Math.cos(rad);
          const isCardinal = deg % 90 === 0;
          const label = svgEl("text", {
            x: lx,
            y: ly,
            "text-anchor": "middle",
            "dominant-baseline": "middle",
            "font-family": "sans-serif",
            "font-size": isCardinal ? "13" : "9",
            "font-weight": isCardinal ? "700" : "500",
            fill: isCardinal
              ? "var(--pstrotator-accent, #ff5a36)"
              : "var(--secondary-text-color, #888)",
          });
          const names = { 0: "N", 90: "E", 180: "S", 270: "W" };
          label.textContent = names[deg] || String(deg);
          tickGroup.appendChild(label);
        }
      }
      svg.appendChild(tickGroup);

      // Home marker
      const homeGroup = svgEl("g");
      homeGroup.appendChild(
        svgEl("circle", {
          cx,
          cy,
          r: 5,
          fill: "var(--pstrotator-home, #ffd84a)",
          stroke: "#6b4e00",
          "stroke-width": 1.2,
        })
      );
      svg.appendChild(homeGroup);

      // Needle (azimuth indicator): a thin line along the circle's radius.
      this._needleLine = svgEl("line", {
        x1: cx,
        y1: cy,
        x2: cx,
        y2: cy - R,
        stroke: cfg.line_color,
        "stroke-width": 1.5,
        "stroke-linecap": "round",
        filter: "url(#needleGlow)",
      });
      svg.appendChild(this._needleLine);
      this._needleDot = svgEl("circle", {
        cx,
        cy: cy - R,
        r: 3,
        fill: cfg.line_color,
      });
      svg.appendChild(this._needleDot);
    }

    _azimuthFromEvent(ev) {
      const rect = this._svg.getBoundingClientRect();
      const viewBox = this._svg.viewBox.baseVal;
      const scaleX = viewBox.width / rect.width;
      const scaleY = viewBox.height / rect.height;
      const x = (ev.clientX - rect.left) * scaleX;
      const y = (ev.clientY - rect.top) * scaleY;
      const dx = x - this._cx;
      const dy = y - this._cy;
      return { az: wrap360(Math.atan2(dx, -dy) / DEG), dist: Math.hypot(dx, dy) };
    }

    _onPointerDown(ev) {
      const { az, dist } = this._azimuthFromEvent(ev);
      if (dist > this._R + 20) return;

      this._svg.setPointerCapture(ev.pointerId);
      this._svg.classList.add("dragging");
      this._dragging = true;
      this._dragAzimuth = az;
      this._renderNeedle(az);
      this._setAzimuth(az);
    }

    _onPointerMove(ev) {
      if (!this._dragging) return;
      const { az } = this._azimuthFromEvent(ev);
      this._dragAzimuth = az;
      this._renderNeedle(az);
      const readout = this.shadowRoot.getElementById("az-readout");
      if (readout) readout.textContent = `${az.toFixed(1)}°`;
      this._setAzimuth(az);
    }

    _onPointerUp(ev) {
      if (!this._dragging) return;
      this._dragging = false;
      this._svg.classList.remove("dragging");
      if (this._svg.hasPointerCapture(ev.pointerId)) {
        this._svg.releasePointerCapture(ev.pointerId);
      }
      if (this._dragAzimuth != null) this._setAzimuth(this._dragAzimuth, true);
    }

    _nudge(delta) {
      const az = wrap360(this._currentAzimuth() + delta);
      this._setAzimuth(az, true);
    }

    _setAzimuth(az, force) {
      if (!this._hass) return;
      const now = Date.now();
      if (!force && now - this._lastSendTime < 150) return;
      this._lastSendTime = now;
      this._hass.callService("number", "set_value", {
        entity_id: this._config.entity,
        value: Math.round(az * 10) / 10,
      });
    }

    _renderNeedle(az) {
      if (!this._needleLine) return;
      const cx = this._cx;
      const cy = this._cy;
      const R = this._R;

      // The needle is always a full radius of the circle; only its
      // direction changes, never its length.
      const rad = az * DEG;
      const tip = { x: cx + R * Math.sin(rad), y: cy - R * Math.cos(rad) };

      this._needleLine.setAttribute("x2", tip.x);
      this._needleLine.setAttribute("y2", tip.y);
      this._needleDot.setAttribute("cx", tip.x);
      this._needleDot.setAttribute("cy", tip.y);
    }

    _updateDynamic() {
      if (!this._svg || !this._needleLine) return;
      const az = this._dragging && this._dragAzimuth != null
        ? this._dragAzimuth
        : this._currentAzimuth();
      const readout = this.shadowRoot.getElementById("az-readout");
      if (readout) readout.textContent = `${az.toFixed(1)}°`;
      this._renderNeedle(az);
    }
  }

  customElements.define("pstrotator-card", PstRotatorCard);

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: "pstrotator-card",
    name: "PstRotator Kaart",
    description:
      "Azimutale wereldkaart om de PstRotator antenne-rotor mee te besturen.",
  });
})();
