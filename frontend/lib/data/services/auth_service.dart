import '../models/user_model.dart';
import 'api_client.dart';

class AuthService {
  /// Login guru — menyimpan JWT token ke storage.
  /// Return [UserModel] jika berhasil.
  Future<UserModel> login(String username, String password) async {
    final data = await ApiClient.post(
      '/auth/login',
      {'username': username.trim(), 'password': password},
      auth: false,
    );
    final token = data['access_token'] as String;
    final user = UserModel.fromJson(data['user'] as Map<String, dynamic>);
    await ApiClient.saveToken(token);
    await ApiClient.saveUserId(user.userId);
    return user;
  }

  /// Register akun guru baru — otomatis login setelah berhasil.
  Future<UserModel> register({
    required String namaLengkap,
    required String username,
    required String password,
    required String confirmPassword,
  }) async {
    final data = await ApiClient.post(
      '/auth/register',
      {
        'full_name': namaLengkap.trim(),
        'username': username.trim(),
        'password': password,
        'confirm_password': confirmPassword,
      },
      auth: false,
    );
    final token = data['access_token'] as String;
    final user = UserModel.fromJson(data['user'] as Map<String, dynamic>);
    await ApiClient.saveToken(token);
    await ApiClient.saveUserId(user.userId);
    return user;
  }

  /// Ambil profil guru yang sedang login.
  Future<UserModel> getProfile() async {
    final data = await ApiClient.get('/auth/profile');
    return UserModel.fromJson(data['user'] as Map<String, dynamic>);
  }

  /// Edit profil guru (nama lengkap dan/atau username).
  Future<UserModel> updateProfile({
    String? namaLengkap,
    String? username,
  }) async {
    final body = <String, dynamic>{};
    if (namaLengkap != null) body['full_name'] = namaLengkap.trim();
    if (username != null) body['username'] = username.trim();
    final data = await ApiClient.put('/auth/profile', body);
    return UserModel.fromJson(data['user'] as Map<String, dynamic>);
  }

  /// Ganti password guru.
  Future<void> changePassword({
    required String oldPassword,
    required String newPassword,
    required String confirmNewPassword,
  }) async {
    await ApiClient.put('/auth/change-password', {
      'old_password': oldPassword,
      'new_password': newPassword,
      'confirm_new_password': confirmNewPassword,
    });
  }

  /// Logout — hapus token dari storage lokal.
  Future<void> logout() async {
    try {
      await ApiClient.post('/auth/logout', {});
    } catch (_) {
      // Lanjutkan hapus token meski request gagal
    } finally {
      await ApiClient.clearToken();
    }
  }
}
