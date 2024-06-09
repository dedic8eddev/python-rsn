function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
}
tinymce.init({
  selector: '#tiny-mce',
  plugins: [
    'code autolink lists link image charmap print preview anchor',
    'searchreplace visualblocks code fullscreen',
    'insertdatetime media table paste code help wordcount'
  ],
  height: 300,
  menubar: false,
  toolbar: 'code | undo redo | bold italic underline strikethrough | fontselect fontsizeselect formatselect | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist | forecolor backcolor removeformat | pagebreak | charmap emoticons | fullscreen  preview save print | insertfile image media template link anchor codesample | ltr rtl',
  image_title: true,
  automatic_uploads: true,
  file_picker_types: 'image',
  file_picker_callback: (cb, value, meta) => {
      const input = document.createElement('input');
      input.setAttribute('type', 'file');
      input.setAttribute('accept', 'image/*');    
      input.addEventListener('change', (e) => {

        const file = e.target.files[0];             
        var formData = new FormData();

        formData.append('image', file, file.name);

        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/api/images/save-image/', true);
        
        function setHeaders(headers){
          for(let key in headers){
              xhr.setRequestHeader(key, headers[key]) 
          }
        }

        var csrf = $("input[name=csrfmiddlewaretoken]").val();

        setHeaders({"csrfmiddlewaretoken":csrf,"X-CSRFToken": getCookie("csrftoken")});
        var spinner = "<div class='spinnerLoading'><div>";

        $("body").append(spinner)
        xhr.onload = function () {              
            if (xhr.status === 200) {
              const reader = new FileReader();
              reader.addEventListener('load', () => {
                const id = 'blobid' + (new Date()).getTime();
                const blobCache =  tinymce.activeEditor.editorUpload.blobCache;
                const base64 = reader.result.split(',')[1];
                const blobInfo = blobCache.create(id, file, base64);
                blobCache.add(blobInfo);
                cb(xhr.responseText.replaceAll('"', ''), { title: xhr.responseText.replaceAll('"', '') });
                $(".spinnerLoading").remove();
              });
              reader.readAsDataURL(file);
            } else {
              console.log("try again!!")
            }
        };
        xhr.send(formData);
      });
    input.click();
  },
});