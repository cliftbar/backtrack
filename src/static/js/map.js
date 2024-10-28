const layerIdPrefix = 'tracks-'
let sources = {};
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
        layerSelector(map, layerIdPrefix);
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

    const blobUrl = guessInputType(url) + URL.createObjectURL(inputBlob);

    await addSourceLayer(sourceName, blobUrl, color)
    await zoomToSources()
}

async function addSourceLayer(sourceName, blobUrl, color) {
    let layerId = layerIdPrefix + sourceName
    await map.addSource(sourceName, {
        'type': 'geojson', 'data': blobUrl,
    });
    await map.addLayer({
        'id': layerId, 'type': 'line', 'source': sourceName, 'minzoom': 0, 'maxzoom': 20, 'paint': {
            'line-color': color, 'line-width': 5
        }
    });
    let isValid = await sourceValid(sourceName);
    if (isValid) {
        // sources.set(sourceName, layerId);
        sources[sourceName] = layerId;
    }
}

async function sourceValid(sourceName) {
    let srcData = await map.getSource(sourceName).getData();
    return typeof srcData.detail === "undefined"
}

async function removeTrack(evt) {
    let tgt = evt.target;
    let layerId = tgt.value;
    const prefixRegexp = new RegExp(`^${layerIdPrefix}`);
    let sourceId = layerId.replace(prefixRegexp, '');
    map.removeLayer(layerId);
    map.removeSource(sourceId);
    delete sources[sourceId]

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


async function zoomToSourceCollection(source) {
    let d = await map.getSource(source).getData();
    let bounds = d.features.reduce((bounds, f) => {
        return bounds.extend(getFeatureBounds(f));
    }, new maplibregl.LngLatBounds(getFeatureBounds(features[0]), getFeatureBounds(features[0])));

    map.fitBounds(bounds, {
        padding: 20
    });
}

async function zoomToSource(source) {
    let d = await map.getSource(source).getData();

    const coordinates = getFlatCoords(d.features[0].geometry);

    // Pass the first coordinates in the LineString to `lngLatBounds` &
    // wrap each coordinate pair in `extend` to include them in the bounds
    // result. A variation of this technique could be applied to zooming
    // to the bounds of multiple Points or Polygon geometries - it just
    // requires wrapping all the coordinates with the extend method.
    let bounds = coordinates.reduce((bounds, coord) => {
        return bounds.extend(coord);
    }, new maplibregl.LngLatBounds(coordinates[0], coordinates[0]));

    map.fitBounds(bounds, {
        padding: 20
    });
}

async function zoomToSourcesOneFeature() {
    var promises = []
    var coords = []
    let src_arr =Object.keys(sources);
    if (src_arr.length == 0) {
        return;
    }
    for (let i = 0; i < src_arr.length; i++) {
        let k = src_arr[i];
        let src = map.getSource(k)
        promises.push(src.getData());
    }

    let res = await Promise.all(promises)
    for (let r of res) {
        coords = coords.concat(getFlatCoords(r.features[0].geometry))
    }
    ;

    let bounds = coords.reduce((bounds, coord) => {
        return bounds.extend(coord);
    }, new maplibregl.LngLatBounds(coords[0], coords[0]));
    map.fitBounds(bounds, {
        padding: 20
    });
}

async function zoomToSources() {
    let promises = []
    let coords = []
    let src_arr = Object.keys(sources);
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
            maxZoom: 19,
            padding: 20
        });
    }
}

async function layerSelector(map, prefix) {
    // Enumerate ids of the layers
    const prefixRegexp = new RegExp(`^${prefix}`);
    const toggleableLayerIds = Object.keys(map.style._layers).filter(name => name.match(prefixRegexp));

    toggleableLayerIds.forEach(layerId => {
        // Make the name nicer
        const sourceName = layerId.replace(prefixRegexp, '');
        if (typeof sources[sourceName] === "undefined") {
            console.log("ERROR No data for " + layerId + " in " + JSON.stringify(sources) + ", skipping")
            return;
        }


        let elmId = "cbx_" + layerId;

        if (!document.getElementById(elmId)) {
            let red = parseInt(map.style.getLayer(layerId).paint.get("line-color").value.value.r * 256);
            let green = parseInt(map.style.getLayer(layerId).paint.get("line-color").value.value.g * 256);
            let blue = parseInt(map.style.getLayer(layerId).paint.get("line-color").value.value.b * 256);

            let rgb = blue | (green << 8) | (red << 16);
            let layerHex = '#' + rgb.toString(16).padStart(6, '0');

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
            label.textContent = sourceName

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
