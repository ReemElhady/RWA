async function load_sites() {
    fetch('/hygienebox/sites/')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Areas:', data);

            const areaDropdown = document.getElementById('site_select');
            data.forEach(area => {
                const option = document.createElement('option');
                option.value = area.id;
                option.textContent = area.name;
                areaDropdown.appendChild(option);
            });
        })
        .catch(error => console.error('Error loading areas:', error));
}
async function load_negiborhoods(id) {
    fetch(`/hygienebox/neighborhoods?area_id=${id}`)
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('neigborhoods:', data);

        const neighborhoodDropdown = document.getElementById('neighborhood_select');
        neighborhoodDropdown.innerHTML = '<option value="">Select Neighborhood</option>'; // Reset dropdown

        data.forEach(n => {
            const option = document.createElement('option');
            option.value = n.id;
            option.textContent = n.name;
            neighborhoodDropdown.appendChild(option);
        });
    })
    .catch(error => console.error('Error loading neighborhoods:', error));
}
document.addEventListener('DOMContentLoaded', () => {
    load_sites();

});
document.getElementById('site_select').addEventListener('change',(e)=>{
    load_negiborhoods(e.target.value);
})