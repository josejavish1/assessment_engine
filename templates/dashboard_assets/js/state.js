/**
 * Sovereign State Manager
 * Handles DTO_STATE and NEXUS_DATA parsing and validation.
 */

window.SovereignState = (function() {
    let _nexusData = {};
    let _dtoState = {};

    function init() {
        try {
            const nexusEl = document.getElementById('nexus-data');
            if (nexusEl) {
                _nexusData = JSON.parse(nexusEl.textContent);
            }

            const dtoEl = document.getElementById('dto-state');
            if (dtoEl) {
                _dtoState = JSON.parse(dtoEl.textContent);
            } else if (_nexusData.dto_state) {
                _dtoState = _nexusData.dto_state;
            }

            console.log("🚀 Sovereign State Initialized", { nexus: !!_nexusData, dto: !!_dtoState });
            window.dispatchEvent(new CustomEvent('sovereign-ready', { detail: { nexus: _nexusData, dto: _dtoState } }));
        } catch (e) {
            console.error("❌ Failed to initialize Sovereign State", e);
        }
    }

    return {
        init,
        get nexus() { return _nexusData; },
        get dto() { return _dtoState; },
        get strategy() { return _nexusData.strategy || {}; },
        get roadmap() { return _nexusData.roadmap || {}; },
        get towers() { return _nexusData.towers || {}; },
        get heatmap() { return _nexusData.heatmap || []; }
    };
})();
