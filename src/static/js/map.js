const trackLayerIdPrefix = 'tracks-'
const pointLayerIdPrefix = 'point-'
let layerSourceMap = {};
const layerTypeColorPropMap = {
    "circle": "circle-color", "line": "line-color"
}
let map = new maplibregl.Map({
    container: 'map', // container id
    // style: 'https://demotiles.maplibre.org/style.json', // style URL
    // https://github.com/nst-guide/osm-liberty-topo
    style: "https://raw.githubusercontent.com/nst-guide/osm-liberty-topo/gh-pages/style.json", center: [-121.69, 45.37], // starting position [lng, lat]
    zoom: 10 // starting zoom
});

map.on("load", async () => {
    await init();
});


async function init() {
    maplibregl.addProtocol('gpx', VectorTextProtocol.VectorTextProtocol);

    document.getElementById("inputTrackColor").value = randomPastelColors()

    map.on('idle', () => {
        // Add the layer selector
        layerSelector(map);
    });

    await loadSearchParams()
    await zoomToSources();
}

async function loadSearchParams() {
    const urlParams = new URLSearchParams(window.location.search);
    let ps = []
    urlParams.getAll("track").forEach((track) => {
        ps.push(trackFromUrl(track, track, randomPastelColors()));
    });
    await Promise.all(ps);
}

function guessInputType(ipt) {
    if (ipt.includes("gpx")) {
        return "gpx://"
    } else if (ipt.includes("json")) {
        return ""
    } else {
        console.error("couldn't identify input type");
    }
}

async function fetchTrack() {
    let url = document.getElementById("inputUrl").value;
    const sourceName = document.getElementById("inputTrackLabel").value || url;
    let color = document.getElementById("inputTrackColor").value;
    await trackFromUrl(url, sourceName, color);
    document.getElementById("inputTrackColor").value = randomPastelColors();
}

async function selectTrack() {
    let target_fi = document.getElementById("slct_selectTrack").value;
    if (target_fi === "") {
        return;
    }
    let target_url = target_fi
    let color = document.getElementById("inputTrackColor").value;

    await trackFromUrl(target_url, target_url, color);

    document.getElementById("inputTrackColor").value = randomPastelColors();
}

async function addTrack() {
    const file = document.getElementById("inputFile").files[0]; // Read first selected file
    const sourceName = document.getElementById("inputTrackLabel").value || file.name;
    let color = document.getElementById("inputTrackColor").value;

    const reader = new FileReader();

    reader.onload = async function (theFile) {

        const gpxContent = theFile.target.result;

        const inputBlob = new Blob([gpxContent], {type: 'text/plain'});
        // Create a data URL from the Blob
        const blobUrl = guessInputType(file.name) + URL.createObjectURL(inputBlob);

        await addSourceLayer(sourceName, blobUrl, color)
        await zoomToSources();
    }
    reader.readAsText(file, 'UTF-8');
}

async function trackFromUrl(url, sourceName, color) {
    let r = await fetch(url)
    let content = await r.text()
    const inputBlob = new Blob([content], {type: 'text/plain'});

    let inputType = guessInputType(url)
    const blobUrl = inputType + URL.createObjectURL(inputBlob);

    await addSourceLayer(sourceName, blobUrl, color)
    await zoomToSources()
}

async function addSourceLayer(sourceName, blobUrl, color) {
    let trackLayerId = trackLayerIdPrefix + sourceName
    await map.addSource(sourceName, {
        'type': 'geojson', 'data': blobUrl,
    });

    let isSourceValid = await sourceValid(sourceName);
    if (!isSourceValid) {
        return
    }

    await map.addLayer({
        'id': trackLayerId, 'type': 'line', 'source': sourceName, 'minzoom': 0, 'maxzoom': 20, 'paint': {
            'line-color': color, 'line-width': 5
        }, 'filter': ['==', '$type', 'LineString']
    });
    layerSourceMap[trackLayerId] = sourceName;

    let sourceType = await sourceTypes(sourceName);
    if (sourceType.includes("Point")) {
        let pointLayerId = pointLayerIdPrefix + sourceName;
        await addPointLayerClick(pointLayerIdPrefix + sourceName, sourceName)
        layerSourceMap[pointLayerId] = sourceName;
    }
}

async function addPointLayerClick(layerId, sourceName) {
    await map.addLayer({
        'id': layerId, 'type': 'circle', 'source': sourceName, 'minzoom': 0, 'maxzoom': 20, 'paint': {
            'circle-color': "red", 'circle-radius': 6
        }, 'filter': ['==', '$type', 'Point']
    });

    // When a click event occurs on a feature in the places layer, open a popup at the
    // location of the feature, with description HTML from its properties.
    map.on('click', layerId, (e) => {
        const coordinates = e.features[0].geometry.coordinates.slice();
        const props = e.features[0].properties;

        // Ensure that if the map is zoomed out such that multiple
        // copies of the feature are visible, the popup appears
        // over the copy being pointed to.
        while (Math.abs(e.lngLat.lng - coordinates[0]) > 180) {
            coordinates[0] += e.lngLat.lng > coordinates[0] ? 360 : -360;
        }

        let htmlContent = `
<p>
    <h1>Current Position</h1>
    <ul>
        <li>time: ${new Date(props.time).toLocaleString()}</li>
        ${typeof props.speed !== 'undefined' ? `<li>speed: ${props.speed}</li>` : ''}
        ${typeof props.direction !== 'undefined' ? `<li>direction: ${props.direction}</li>` : ''}
        ${typeof props.distance !== 'undefined' ? `<li>distance: ${props.distance}</li>` : ''}
        ${typeof props.battery !== 'undefined' ? `<li>battery: ${props.battery}</li>` : ''}
        ${typeof props.accuracy !== 'undefined' ? `<li>accuracy: ${Math.round(props.accuracy)}</li>` : ''}
    </ul>
</p>
`
        new maplibregl.Popup()
            .setLngLat(coordinates)
            .setHTML(htmlContent)
            .addTo(map);
    });

    // Change the cursor to a pointer when the mouse is over the places layer.
    map.on('mouseenter', layerId, () => {
        map.getCanvas().style.cursor = 'pointer';
    });

    // Change it back to a pointer when it leaves.
    map.on('mouseleave', layerId, () => {
        map.getCanvas().style.cursor = '';
    });
}


async function sourceValid(sourceName) {
    let srcData = await map.getSource(sourceName).getData();
    return typeof srcData.detail === "undefined"
}

async function sourceTypes(sourceName) {
    let srcData = await map.getSource(sourceName).getData();

    return srcData.features.flatMap(f => f.geometry).map(g => g.type)
}

async function removeTrack(evt) {
    let tgt = evt.target;
    let layerId = tgt.value;

    let sourceId = layerSourceMap[layerId];
    map.removeLayer(layerId);

    delete layerSourceMap[layerId]
    let src_arr = Array.from(new Set(Object.values(layerSourceMap)));
    if (!src_arr.includes(sourceId)) {
        map.removeSource(sourceId);
    }

    let elmId = "cbx_" + layerId;
    document.getElementById("li_" + elmId).remove();
}

function getFlatCoords(geom) {
    if (geom.type == "LineString") {
        return geom.coordinates;
    } else if (geom.type == "MultiLineString") {
        return geom.coordinates.flat();
    } else if (geom.type == "Point") {
        return [geom.coordinates];
    }
    return geom.coordinates;
}

function getFeatureBounds(feature) {
    const coordinates = getFlatCoords(feature.geometry);

    // Pass the first coordinates in the LineString to `lngLatBounds` &
    // wrap each coordinate pair in `extend` to include them in the bounds
    // result. A variation of this technique could be applied to zooming
    // to the bounds of multiple Points or Polygon geometries - it just
    // requires wrapping all the coordinates with the extend method.
    let bounds = coordinates.reduce((bounds, coord) => {
        return bounds.extend(coord);
    }, new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));

    return bounds;
}

async function zoomToSources() {
    let promises = []
    let coords = []
    let src_arr = Array.from(new Set(Object.values(layerSourceMap)));
    if (src_arr.length === 0) {
        return;
    }
    for (let i = 0; i < src_arr.length; i++) {
        let k = src_arr[i];
        let src = map.getSource(k)
        promises.push(src.getData());
    }

    let res = await Promise.all(promises)
    for (let r of res) {
        if (typeof r.detail !== "undefined") {
            console.log("Track Error: " + r.detail)
            continue
        }
        for (let f of r.features) {
            coords = coords.concat(getFeatureBounds(f));
        }
    }
    ;

    let bounds = coords.reduce((bounds, coord) => {
        return bounds.extend(coord.toArray());
    }, coords[0]);
    if (typeof bounds !== "undefined") {
        map.fitBounds(bounds, {
            maxZoom: 19, padding: 20
        });
    }
}

async function layerSelector(map) {
    // Enumerate ids of the layers
    const toggleableLayerIds = Object.keys(map.style._layers).filter(name => name.startsWith(trackLayerIdPrefix) || name.startsWith(pointLayerIdPrefix));

    toggleableLayerIds.forEach(layerId => {
        // Make the name nicer
        let textName = layerId
        if (typeof layerSourceMap[layerId] === "undefined") {
            console.log("ERROR No data for " + layerId + " in " + JSON.stringify(layerSourceMap) + ", skipping")
            return;
        }


        let elmId = "cbx_" + layerId;

        if (!document.getElementById(elmId)) {
            let mapLayer = map.style.getLayer(layerId)
            let layerHex = map.getPaintProperty(layerId, layerTypeColorPropMap[mapLayer.type]);

            // Create a link.
            let link = document.createElement('input');
            link.id = elmId;
            link.type = "checkbox"
            link.className = 'active';
            link.value = layerId
            link.checked = true

            let label = document.createElement("label")
            label.id = "lbl_" + elmId
            label.htmlFor = elmId
            label.textContent = textName

            let btn = document.createElement("button")
            btn.id = "btn_" + elmId
            btn.type = "button";
            btn.onclick = removeTrack;
            btn.textContent = "X"
            btn.value = layerId
            btn.style = "background: " + layerHex;

            // Show or hide layer when the toggle is clicked.
            link.onchange = async function (e) {
                const clickedLayer = this.value;
                e.preventDefault();
                e.stopPropagation();

                const visibility = map.getLayoutProperty(clickedLayer, 'visibility');

                // Toggle layer visibility by changing the layout object's visibility property.
                if (visibility !== 'none') {
                    map.setLayoutProperty(clickedLayer, 'visibility', 'none');
                    this.className = '';
                } else {
                    this.className = 'active';
                    map.setLayoutProperty(clickedLayer, 'visibility', 'visible');
                }
            };

            const layers = document.getElementById('track-list');
            let li = document.createElement("li")
            li.id = "li_" + elmId
            li.appendChild(link);
            li.appendChild(label)
            li.appendChild(btn)
            layers.appendChild(li)
        }
    });
}

// https://stackoverflow.com/questions/43044/algorithm-to-randomly-generate-an-aesthetically-pleasing-color-palette
function randomPastelColors() {
    let color = [191, 191, 191]
    var r = (Math.round(((Math.random() * 256) + color[0]) / 2)).toString(16);
    var g = (Math.round(((Math.random() * 256) + color[1]) / 2)).toString(16);
    var b = (Math.round(((Math.random() * 256) + color[2]) / 2)).toString(16);
    let res = '#' + r + g + b;
    return res
}
