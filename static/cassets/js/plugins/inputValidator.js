class InputValidator {
  constructor(inputElement, errorElement, options = {}) {
    this.input = inputElement;
    this.errorElement = errorElement;
    this.options = options;

    // Thêm sự kiện onchange
    if (this.options.validateOnChange) {
      this.input.addEventListener('input', this.validateOnChange.bind(this));
      this.input.addEventListener('change', this.validateOnChange.bind(this));
    }
  }

  // Validate khi có thay đổi
  validateOnChange() {
    if (this.options.validateRequired && !this.validateRequired()) return;
    if (this.options.validateEmail && !this.validateEmail()) return;
    if (this.options.validatePhone && !this.validatePhone()) return;
    if (this.options.validateNumber && !this.validateNumber()) return;
    if (this.options.validateUrl && !this.validateUrl()) return;
    if (this.options.validateDate && !this.validateDate()) return;
    if (this.options.validateTime && !this.validateTime()) return;
    if (this.options.validatePassword && !this.validatePassword()) return;
    if (this.options.validateConfirmPassword && !this.validateConfirmPassword()) return;
    if (this.options.minLength && !this.validateLength(this.options.minLength, this.options.maxLength)) return;
    if (this.options.validatePattern && !this.validatePattern(this.options.pattern)) return;
    if (this.options.validateFileType && !this.validateFileType(this.options.allowedTypes)) return;
    if (this.options.validateFileSize && !this.validateFileSize(this.options.maxSize)) return;
    if (this.options.validateCheckbox && !this.validateCheckbox()) return;
    if (this.options.validateRadio && !this.validateRadio()) return;
    if (this.options.validateSelect && !this.validateSelect()) return;
  }

  // Các phương thức validate
  validateRequired() {
    const value = this.input.value.trim();
    if (!value) {
      this.showError('Trường này là bắt buộc');
      return false;
    }
    this.clearError();
    return true;
  }

  validateEmail() {
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(this.input.value)) {
      this.showError('Email không hợp lệ');
      return false;
    }
    this.clearError();
    return true;
  }

  validatePhone() {
    const phonePattern = /^[0-9]{10,11}$/;
    if (!phonePattern.test(this.input.value)) {
      this.showError('Số điện thoại không hợp lệ');
      return false;
    }
    this.clearError();
    return true;
  }

  validateNumber() {
    if (isNaN(this.input.value)) {
      this.showError('Vui lòng nhập số');
      return false;
    }
    this.clearError();
    return true;
  }

  validateUrl() {
    const urlPattern = /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/;
    if (!urlPattern.test(this.input.value)) {
      this.showError('URL không hợp lệ');
      return false;
    }
    this.clearError();
    return true;
  }

  validateDate() {
    const datePattern = /^\d{4}-\d{2}-\d{2}$/;
    if (!datePattern.test(this.input.value)) {
      this.showError('Ngày không hợp lệ (YYYY-MM-DD)');
      return false;
    }
    this.clearError();
    return true;
  }

  validateTime() {
    const timePattern = /^([01]?[0-9]|2[0-3]):[0-5][0-9]$/;
    if (!timePattern.test(this.input.value)) {
      this.showError('Thời gian không hợp lệ (HH:MM)');
      return false;
    }
    this.clearError();
    return true;
  }

  validatePassword() {
    if (this.input.value.length < 8) {
      this.showError('Mật khẩu phải có ít nhất 8 ký tự');
      return false;
    }
    this.clearError();
    return true;
  }

  validateConfirmPassword(confirmInput) {
    if (this.input.value !== confirmInput.value) {
      this.showError('Mật khẩu không khớp');
      return false;
    }
    this.clearError();
    return true;
  }

  validateLength(min, max) {
    const length = this.input.value.length;
    if (min && length < min) {
      this.showError(`Phải có ít nhất ${min} ký tự`);
      return false;
    }
    if (max && length > max) {
      this.showError(`Không được vượt quá ${max} ký tự`);
      return false;
    }
    this.clearError();
    return true;
  }

  validatePattern(pattern) {
    if (!pattern.test(this.input.value)) {
      this.showError('Giá trị không hợp lệ');
      return false;
    }
    this.clearError();
    return true;
  }

  validateFileType(allowedTypes) {
    const file = this.input.files[0];
    if (file && !allowedTypes.includes(file.type)) {
      this.showError(`Chỉ chấp nhận file ${allowedTypes.join(', ')}`);
      return false;
    }
    this.clearError();
    return true;
  }

  validateFileSize(maxSize) {
    const file = this.input.files[0];
    if (file && file.size > maxSize) {
      this.showError(`File không được lớn hơn ${maxSize / 1024 / 1024}MB`);
      return false;
    }
    this.clearError();
    return true;
  }

  validateCheckbox() {
    if (!this.input.checked) {
      this.showError('Vui lòng chọn ô này');
      return false;
    }
    this.clearError();
    return true;
  }

  validateRadio() {
    const radios = document.querySelectorAll(`input[name="${this.input.name}"]`);
    if (!Array.from(radios).some(radio => radio.checked)) {
      this.showError('Vui lòng chọn một tùy chọn');
      return false;
    }
    this.clearError();
    return true;
  }

  validateSelect() {
    if (this.input.value === '') {
      this.showError('Vui lòng chọn một tùy chọn');
      return false;
    }
    this.clearError();
    return true;
  }

  showError(message) {
    this.errorElement.textContent = message;
    this.errorElement.style.display = 'block';
    this.input.classList.add('error');
  }

  clearError() {
    this.errorElement.textContent = '';
    this.errorElement.style.display = 'none';
    this.input.classList.remove('error');
  }
}

// Cách sử dụng mới:
// const input = document.getElementById('myInput');
// const error = document.getElementById('errorMessage');
// const validator = new InputValidator(input, error, {
//   validateOnChange: true,
//   validateRequired: true,
//   validateEmail: true,
//   minLength: 5,
//   maxLength: 10,
//   validateNumber: true,
//   validateUrl: true,
//   validateDate: true,
//   validateTime: true,
//   validatePassword: true,
//   validateConfirmPassword: true,
//   validatePattern: /^[a-zA-Z0-9]+$/,
//   validateFileType: ['image/jpeg', 'image/png'],
//   validateFileSize: 5 * 1024 * 1024, // 5MB
//   validateCheckbox: true,
//   validateRadio: true,
//   validateSelect: true
// });