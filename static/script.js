document.addEventListener("DOMContentLoaded", () => {
    const simForm = document.getElementById("simForm");
    const btnSim = document.getElementById("btnSim");
    const placeholderState = document.getElementById("placeholderState");
    const loadingState = document.getElementById("loadingState");
    const activeState = document.getElementById("activeState");
    const resMetaSport = document.getElementById("resMetaSport");
    const resNameA = document.getElementById("resNameA");
    const resPtsA = document.getElementById("resPtsA");
    const resNameB = document.getElementById("resNameB");
    const resPtsB = document.getElementById("resPtsB");
    const resProbA = document.getElementById("resProbA");
    const resProbB = document.getElementById("resProbB");
    const historyLogContainer = document.getElementById("historyLogContainer");

    syncHistoryLogs();

    simForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const sport = document.getElementById("sport").value;
        const teamA = document.getElementById("teamA").value.trim();
        const teamB = document.getElementById("teamB").value.trim();

        placeholderState.classList.add("hidden");
        loadingState.classList.remove("hidden");
        activeState.classList.add("hidden");
        btnSim.disabled = true;

        try {
            const response = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sport: sport, team_a: teamA, team_b: teamB })
            });
            if(!response.ok) {
                const errData = await response.json();
                throw new Error(errData.error || "Processing failure.");
            }
            const data = await response.json();
            resMetaSport.innerText = `${sport} Simulation Complete`;
            resNameA.innerText = data.teams.a;
            resNameB.innerText = data.teams.b;
            resPtsA.innerText = data.simulation.proj_pts_a;
            resPtsB.innerText = data.simulation.proj_pts_b;
            resProbA.innerText = `${Math.round(data.simulation.win_prob_a * 100)}%`;
            resProbB.innerText = `${Math.round(data.simulation.win_prob_b * 100)}%`;

            loadingState.classList.add("hidden");
            activeState.classList.remove("hidden");
            syncHistoryLogs();
        } catch (err) {
            alert(`Simulation Failed: ${err.message}`);
            placeholderState.classList.remove("hidden");
            loadingState.classList.add("hidden");
        } finally {
            btnSim.disabled = false;
        }
    });

    async function syncHistoryLogs() {
        try {
            const res = await fetch('/history');
            if(!res.ok) return;
            const rows = await res.json();
            if(!rows || rows.length === 0) {
                historyLogContainer.innerHTML = '<tr><td class="py-3 text-slate-500 italic">No historical records found.</td></tr>';
                return;
            }
            historyLogContainer.innerHTML = rows.map(r => `
                <tr class="hover:bg-slate-900/40">
                    <td class="py-2.5 font-bold text-slate-400 mono">${r.sport}</td>
                    <td class="py-2.5 text-slate-200">${r.team_a} vs ${r.team_b}</td>
                    <td class="py-2.5 text-right text-emerald-400 font-medium">Winner: ${r.winner}</td>
                </tr>
            `).join('');
        } catch (e) { console.error(e); }
    }
});
