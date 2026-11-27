function renderVisual(target, data) {
    const cut = 34;
    const groups = new Map();
    for (const row of data.rows) {
        if (!groups.has(row.zone)) groups.set(row.zone,[]);
        groups.get(row.zone).push(row.estimate);
    }
    const sheets = node('div',undefined,'shelf-lines');
    for (const [name, hours] of groups) {
        const long = hours.filter(value => value >= cut).length;
        const median = [...hours].sort((a,b) => a-b)[Math.floor(hours.length / 2)];
        const row = node('article',undefined,'shelf-note');
        row.append(node('span',name),node('strong',`${format.format(median)} 小时`),node('span',`${long} / ${hours.length} 单达到 ${cut} 小时`));
        sheets.append(row);
    }
    target.append(sheets);
}
