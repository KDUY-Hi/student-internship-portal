import React, { useState } from 'react';
import { api, friendlyError } from '../api/client';
import { Logo } from './ui';
import heroImage from '../assets/hero-internship.png';

export function AuthPanel({ mode, setMode, onAuth, setMessage }) {
  const [form, setForm] = useState({ name: '', email: '', password: '', role: 'student' });
  const [submitting, setSubmitting] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    try {
      const data = await api(mode === 'login' ? '/auth/login' : '/auth/register', {
        method: 'POST',
        body: mode === 'login' ? { email: form.email, password: form.password } : form,
      });
      onAuth(data);
    } catch (error) {
      setMessage(friendlyError(error));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="auth-layout">
      <div className="auth-intro">
        <Logo />
        <div className="auth-copy">
          <h1>Chào mừng bạn đến với TopCV</h1>
          <p>Nền tảng tuyển dụng và tìm việc hàng đầu dành cho sinh viên thực tập.</p>
        </div>
        <img src={heroImage} alt="Ứng viên tìm kiếm thực tập" />
      </div>

      <form className="auth-card" onSubmit={submit}>
        <div className="auth-tabs">
          <button className={mode === 'login' ? 'active' : ''} type="button" onClick={() => setMode('login')}>Đăng nhập</button>
          <button className={mode === 'register' ? 'active' : ''} type="button" onClick={() => setMode('register')}>Đăng ký</button>
        </div>

        {mode === 'register' && (
          <>
            <label>Họ và tên<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
            <label>
              Vai trò
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}>
                <option value="student">Ứng viên</option>
                <option value="company">Nhà tuyển dụng</option>
              </select>
            </label>
          </>
        )}

        <label>Email<input type="email" placeholder="Nhập email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
        <label>Mật khẩu<input type="password" placeholder="Nhập mật khẩu" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></label>

        <button className="primary full" type="submit" disabled={submitting}>{submitting ? 'Đang xử lý...' : mode === 'login' ? 'Đăng nhập' : 'Tạo tài khoản'}</button>
        <p className="switch-mode">
          {mode === 'login' ? 'Chưa có tài khoản?' : 'Đã có tài khoản?'}
          <button type="button" onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'Đăng ký ngay' : 'Đăng nhập'}</button>
        </p>
      </form>
    </section>
  );
}
