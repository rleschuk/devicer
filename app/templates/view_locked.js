
function generate_columns(cols) {
  let columns = [];
  let specials = ['rowid','task_id','task_date','task_error','task_result','task_state','username','password'];
  cols.forEach(function(item, index) {
    let visible = true;
    let name = item;
    if (typeof item === 'object' && item !== null && !(item instanceof Array) && !(item instanceof Date)) {
      visible = item.visible;
      name = item.name;
    }
    if (!specials.includes(name)) {
      columns.push({
        data: name,
        title: name.charAt(0).toUpperCase() + name.slice(1),
        name: name,
        visible: visible,
        class: 'col_' + name
      });
    }
  });
  columns.unshift({data: 'rowid', title: 'Rowid', name: 'rowid', class: 'col_rowid', visible: false});
  columns.push({data: 'task_id', title: 'Task_id', name: 'task_id', class: 'col_task_id', visible: true,
    render: function(data, type, row, meta) {
      if (type === 'display') {
        data = '<a href="{{url_for("main.task_log", task_id="id")}}" \
          target="_blank" style="font-family:monospace;font-size:90%;">'
          .replace('/id', '/' + data) + data + '</a>';
      }
      return data;
    }
  });
  columns.push({data: 'task_date', title: 'Task_date', name: 'task_date', class: 'col_task_date'});
  columns.push({data: 'task_error', title: 'Task_error', name: 'task_error', class: 'col_task_error'});
  columns.push({data: 'task_result', title: 'Task_result', name: 'task_result', class: 'col_task_result',
    render: function(data, type, row, meta) {
      if (type === 'display') {
        data = '<div style="font-family:monospace;font-size:90%;">';
        if (row.task_result) {
          let keys = Object.keys(row.task_result);
          if (keys.length == 1) {
            data += row.task_result[keys[0]]
          } else {
            for (var i in keys) {
              if (i == 1) { data += '\n\n'; }
              data += '<b>' + keys[i] + ':</b>\n';
              data += row.task_result[keys[i]]
            }
          }
        }
        data += '</div>';
        data = data.replace(/\n/g, "<br />");
      }
      return data;
    }
  });
  columns.push({data: 'task_state', title: 'Task_state', name: 'task_state', class: 'col_task_state',
    render: function(data, type, row, meta) {
      if (type === 'display') {
        if (typeof row.task_state === 'undefined' || row.task_state === null) { row.task_state = 'NORUN' }
        data = $('<button type="button" disabled>')
          .attr('class', 'btn btn-block')
          .text(row.task_state)
        if (row.task_state === 'SUCCESS') { data.addClass('btn-outline-success'); }
        if (row.task_state === 'FAILURE') { data.addClass('btn-danger'); }
        data = data.get(0).outerHTML;
      }
      return data;
    }
  });
  cols.forEach(function(col, index) {
    if (typeof col === 'object' && col !== null && !(col instanceof Array) && !(col instanceof Date)) {
      columns.forEach(function(col_, index) {
        if (col_.name === col.name) { columns[index].visible = col.visible; return; }
      });
    }
  });

  return columns;
}

function unlock(target) {
  bootbox.prompt("Enter lock password", function(lock_password) {
    console.log(lock_password);
    if (lock_password) {
      $.ajax({
        type: "POST",
        url: '{{ url_for("main.lock", view_key=view_key) }}',
        data: JSON.stringify({
          lock: false,
          lock_password: lock_password
        }),
        contentType: "application/json; charset=utf-8",
        dataType: 'json'
      }).done(function(data) {
        location.reload();
      }).fail(function(xhr, status, error) {
        console.error(error, xhr.responseText);
        bootbox.alert(xhr.responseText);
      });
    } else { return }
  });
}
