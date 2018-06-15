
function exec_select(target) {
  if (processing == true) { return };
  processing = true;
  $(target).html('<i class="fas fa-spinner faa-spin animated"></i>').prop('disabled', true);
  $.ajax({
    type: "POST",
    url: '{{url_for("main.exec_select")}}',
    data: JSON.stringify({
      rows: data_table.rows().data().toArray(),
      code: devicer_code.getValue()
    }),
    contentType: "application/json; charset=utf-8",
    dataType: 'json'
  }).done(function(data) {
    data.forEach(function(row, i) {
      data_table.row(function (idx, data, node) {return data.rowid === row.rowid}).data(row);
    });
    ajax_process = $.ajax({
      type: 'POST',
      url: '{{ url_for("main.tasks") }}',
      data: JSON.stringify(data),
      contentType: "application/json; charset=utf-8",
      dataType: 'json',
      processData: true,
      xhrFields: {
        onprogress: function(e) {
          let response = e.currentTarget.response.trim().split("\n");
          try {
            response.forEach(function(item) {
              item = JSON.parse(item);
              let row = data_table.row(function (idx, data, node) {
                return data.task_id === item.task_id ? true : false;
              });
              for (let col_name in item) {
                try { data_table.cell(row, col_name + ':name').data(item[col_name]); }
                catch {}
              }
            });
          } catch(err) {}
        }
      }
    }).done(function() {
      processing = false;
      $(target).html('<i class="far fa-play-circle"></i> Запустить').prop('disabled', false);
    }).fail(function() {
      processing = false;
      $(target).html('<i class="far fa-play-circle"></i> Запустить').prop('disabled', false);
    });
  }).fail(function(xhr, status, error) {
    processing = false;
    $(target).html('<i class="far fa-play-circle"></i> Запустить').prop('disabled', false);
    console.error(error, xhr.responseText);
    bootbox.alert(xhr.responseText);
  })
}

function exec_errors(target) {
  if (processing == true) { return };
  rows = data_table.rows(function(idx, data, node) {return data.task_state === 'FAILURE'});
  if (rows.count() > 0) {
    processing = true;
    $(target).html('<i class="fas fa-spinner faa-spin animated"></i>').prop('disabled', true);
    $.ajax({
      type: "POST",
      url: '{{url_for("main.exec_select")}}',
      data: JSON.stringify({
        rows: rows.data().toArray(),
        code: devicer_code.getValue()
      }),
      contentType: "application/json; charset=utf-8",
      dataType: 'json'
    }).done(function(data) {
      data.forEach(function(row, i) {
        data_table.row(function(idx, data, node) {return data.rowid === row.rowid}).data(row);
      });
      ajax_process = $.ajax({
        type: 'POST',
        url: '{{ url_for("main.tasks") }}',
        data: JSON.stringify(data),
        contentType: "application/json; charset=utf-8",
        dataType: 'json',
        processData: true,
        xhrFields: {
          onprogress: function(e) {
            let response = e.currentTarget.response.trim().split("\n");
            try {
              response.forEach(function(item) {
                item = JSON.parse(item);
                let row = data_table.row(function (idx, data, node) {
                  return data.task_id === item.task_id ? true : false;
                });
                for (let col_name in item) {
                  try { data_table.cell(row, col_name + ':name').data(item[col_name]); }
                  catch {}
                }
              })
            } catch(err) {}
          }
        }
      }).done(function() {
        processing = false;
        $(target).html('<i class="far fa-play-circle"></i> Запустить по ошибкам').prop('disabled', false);
      }).fail(function() {
        processing = false;
        $(target).html('<i class="far fa-play-circle"></i> Запустить по ошибкам').prop('disabled', false);
      });
    }).fail(function(xhr, status, error) {
      processing = false;
      $(target).html('<i class="far fa-play-circle"></i> Запустить по ошибкам').prop('disabled', false);
      console.error(error, xhr.responseText);
      bootbox.alert(xhr.responseText);
    })
  }
}

function exec_device(target) {
  if (processing == true) { return };
  let tr = $(target).closest('tr');
  let row = data_table.row(tr);
  let row_data = row.data();
  if ($(target).text() == 'PENDING') {
    $.ajax({
      url: '{{ url_for("main.task_info", task_id="string") }}'
        .replace('/string', '/' + row_data.task_id),
      async: true,
      dataType: 'json'
    }).done(function(data) {
      for (let col_name in data) {
        try { data_table.cell(row, col_name + ':name').data(data[col_name]); }
        catch {}
      }
    }).fail(function(xhr, status, error) {
      console.error(error, xhr.responseText);
      bootbox.alert(xhr.responseText);
    });
  } else {
    $.ajax({
      type: "POST",
      url: '{{url_for("main.exec_device")}}',
      data: JSON.stringify({
        row: row_data,
        code: devicer_code.getValue()
      }),
      contentType: "application/json; charset=utf-8",
      dataType: 'json'
    }).done(function(data) {
      data_table.cell(row,'task_id:name').data(data.task_id);
      data_table.cell(row,'task_state:name').data(data.task_state);
      let timer = setInterval(function() {
        $.ajax({
          url: '{{ url_for("main.task_info", task_id="string") }}'
            .replace('/string', '/' + data.task_id),
          async: true,
          dataType: 'json'
        }).done(function(data) {
          if (data.task_state !== 'PENDING') {
            for (let col_name in data) {
              try { data_table.cell(row, col_name + ':name').data(data[col_name]); }
              catch {}
            }
            clearInterval(timer);
          }
        }).fail(function(xhr, status, error) {
          clearInterval(timer);
          console.error(error, xhr.responseText);
          bootbox.alert(xhr.responseText);
        });
      }, 5000);
    });
  }
}

function generate_columns(cols) {
  let columns = [];
  let specials = ['rowid','task_id','task_date','task_error','task_result','task_state'];
  cols.forEach(function(item, index) {
    let visible = true;
    let name = item;
    if (typeof item === 'object' && item !== null && !(item instanceof Array) && !(item instanceof Date)) {
      visible = item.visible;
      name = item.name;
    }
    if (!specials.includes(name)) {
      let col = {
        data: name,
        title: name.charAt(0).toUpperCase() + name.slice(1),
        name: name,
        visible: visible,
        class: 'col_' + name
      };
      if (name === 'username' || name === 'password') {
        col.render = function(data, type, row, meta) {
          if (type === 'display') {
            data = '<input class="form-control" name="' + meta.settings.aoColumns[meta.col].name + '" \
            type="text" style="padding:4px;" value="' + (data == null ? '': data) + '">';
          }
          return data;
        }
      }
      columns.push(col);
    }
  });
  columns.unshift({data: 'rowid', title: 'Rowid', name: 'rowid', class: 'col_rowid'});
  columns.push({data: 'task_id', title: 'Task_id', name: 'task_id', class: 'col_task_id',
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
              data += row.task_result[keys[i]];
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
        data = $('<button type="button">')
          .attr('class', 'btn btn-block')
          .attr('onclick', 'exec_device(this)')
          .text(row.task_state)
        if (row.task_state === 'SUCCESS') { data.addClass('btn-outline-success'); }
        if (row.task_state === 'FAILURE') { data.addClass('btn-danger'); }
        data = data.get(0).outerHTML;
      }
      return data;
    }
  });

  return columns;
}

function select_data(target) {
  if (processing == true) { return };
  processing = true;
  $(target).html('<i class="fas fa-spinner faa-spin animated"></i>').prop('disabled', true);

  if ($("input[name='selecter_mode']:checked").attr('mode') == 'python') {

    try {
      let data = JSON.parse(devicer_select.getValue());
      load_data(data);
    } catch(err) {
      alert(err);
    }
    processing = false;
    $(target).html('<i class="fas fa-table"></i> Загрузить данные').prop('disabled', false);

  } else if ($("input[name='selecter_mode']:checked").attr('mode') == 'sql') {

    let columns = get_columns_settings();
    $.ajax({
      type: "POST",
      url: '{{url_for("main.execute_sql")}}',
      data: JSON.stringify({
        sql: devicer_select.getValue(),
        current: data_table != null ? data_table.rows().data().toArray() : null
      }),
      contentType: "application/json; charset=utf-8",
      dataType: 'json'
    }).done(function(data) {
      load_data(data);
      set_columns_settings(columns);
      processing = false;
      $(target).html('<i class="fas fa-table"></i> Загрузить данные').prop('disabled', false);
    }).fail(function(xhr, status, error) {
      processing = false;
      $(target).html('<i class="fas fa-table"></i> Загрузить данные').prop('disabled', false);
      console.error(error, xhr.responseText);
      bootbox.alert(xhr.responseText);
    });

  } else if ($("input[name='selecter_mode']:checked").attr('mode') == 'simple') {

    let data = devicer_select.getValue().trim().split('\n');
    data = data.reduce(function(map, obj) {
      map.push({'address': obj});
      return map;
    }, []);
    load_data(data);
    processing = false;
    $(target).html('<i class="fas fa-table"></i> Загрузить данные').prop('disabled', false);

  }
}

function get_columns_settings() {
  columns = {};
  if (data_table) {
    let cols = data_table != null ? data_table.settings().init().columns : null;
    data_table.columns().every(function() {
      columns[cols[this.index()].name] = {visible: data_table.column(this).visible()}
    });
  }
  return columns;
}

function get_data() {
  let rows = [];
  let columns = [];
  if (data_table) {
    rows = data_table.rows().data().toArray();
    let cols = data_table.settings().init().columns;
    data_table.columns().every(function() {
      columns.push(cols[this.index()].name);
    });
  }
  return {columns: columns, rows: rows}
}

function get_settings() {
  return {
    selecter: {
      mode: $('input[name="selecter_mode"]:checked').attr('mode'),
      code: devicer_select.getValue() },
    devicer: {
      code: devicer_code.getValue() },
    columns: get_columns_settings()
  }
}

function save_state() {
  $.ajax({
    type: "POST",
    url: '{{ url_for("main.save_view", view_key=view_key) }}',
    data: JSON.stringify({
      view_name: $('#view_name').val(),
      selecter_mode: $('input[name="selecter_mode"]:checked').attr('mode'),
      selecter_code: devicer_select.getValue(),
      devicer_code: devicer_code.getValue(),
      data: get_data(),
      crontab_enabled: $('#crontab_enabled').prop('checked'),
      crontab: $('#crontab').val(),
      settings: get_settings()
    }),
    contentType: "application/json; charset=utf-8",
    dataType: 'json'
  }).fail(function(xhr, status, error) {
    console.error(error, xhr.responseText);
    bootbox.alert(xhr.responseText);
  });
}

function lock(target) {
  bootbox.prompt("Enter lock password", function(lock_password) {
    console.log(lock_password);
    if (lock_password) {
      $.ajax({
        type: "POST",
        url: '{{ url_for("main.lock", view_key=view_key) }}',
        data: JSON.stringify({
          lock: true,
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

window.onbeforeunload = function () {
  return "Important: Please click on 'Save' button to leave this page.";
};
