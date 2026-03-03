odoo.define("mudanzas_crm.province_widget", function (require) {
  "use strict";

  const SelectionWidget = require("web.relational_fields").SelectionWidget;
  const core = require("web.core");

  const MudanzasProvinceWidget = SelectionWidget.extend({
    /**
     * Map of Estados to their provincias (same as in Python model)
     */
    STATE_PROVINCE_MAP: {
      Andalucía: [
        "Almería",
        "Cádiz",
        "Córdoba",
        "Granada",
        "Huelva",
        "Jaén",
        "Málaga",
        "Sevilla",
      ],
      Aragón: ["Huesca", "Teruel", "Zaragoza"],
      Asturias: ["Principado de Asturias"],
      Baleares: ["Islas Baleares"],
      Canarias: ["Las Palmas", "Santa Cruz de Tenerife"],
      Cantabria: ["Cantabria"],
      "Castilla-La Mancha": [
        "Albacete",
        "Ciudad Real",
        "Cuenca",
        "Guadalajara",
        "Toledo",
      ],
      "Castilla y León": [
        "Ávila",
        "Burgos",
        "León",
        "Palencia",
        "Salamanca",
        "Segovia",
        "Soria",
        "Valladolid",
        "Zamora",
      ],
      Cataluña: ["Barcelona", "Girona", "Lleida", "Tarragona"],
      "Comunidad Valenciana": ["Alicante", "Castellón", "Valencia"],
      Extremadura: ["Badajoz", "Cáceres"],
      Galicia: ["A Coruña", "Lugo", "Ourense", "Pontevedra"],
      Madrid: ["Comunidad de Madrid"],
      Murcia: ["Región de Murcia"],
      Navarra: ["Comunidad Foral de Navarra"],
      "País Vasco": ["Álava", "Guipúzcoa", "Vizcaya"],
      "La Rioja": ["La Rioja"],
    },

    /**
     * Get the corresponding state field name for this province field
     * e.g., 'province_up' -> 'state_up'
     */
    _getStateFieldName: function () {
      const fieldName = this.field.name;
      if (fieldName === "province_up") {
        return "state_up";
      } else if (fieldName === "province_down") {
        return "state_down";
      }
      return null;
    },

    /**
     * Filter available province options based on the selected state
     */
    _filterProvincesByState: function () {
      const stateFieldName = this._getStateFieldName();
      if (!stateFieldName) return;

      const stateValue = this.record.data[stateFieldName];
      const provinces = this.STATE_PROVINCE_MAP[stateValue] || [];

      if (this.$field && this.$field.is("select")) {
        // Re-enable all options first
        this.$field.find("option").show();

        // Hide options that don't match the selected state
        this.$field.find("option").each((idx, opt) => {
          const optValue = opt.value;
          if (optValue && !provinces.includes(optValue)) {
            opt.hidden = true;
          }
        });

        // If current value is not in the filtered list, clear it
        if (this.value && !provinces.includes(this.value)) {
          this.value = false;
          this.$field.val("");
        }
      }
    },

    /**
     * Called when the widget is rendered
     */
    on_attach_callback: function () {
      this._super(...arguments);
      this._filterProvincesByState();

      // Listen for state field changes
      const stateFieldName = this._getStateFieldName();
      if (stateFieldName) {
        this.record.on(
          "change:" + stateFieldName,
          this,
          this._filterProvincesByState,
        );
      }
    },
  });

  return MudanzasProvinceWidget;
});
