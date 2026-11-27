import 'package:flutter/foundation.dart';
import '../data/models/user_model.dart';
import '../data/services/auth_service.dart';
import '../data/services/api_client.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

/// Provider global untuk state autentikasi guru.
/// Wrap MaterialApp dengan ChangeNotifierProvider<AuthProvider>.
class AuthProvider extends ChangeNotifier {
  final _authService = AuthService();

  AuthStatus _status = AuthStatus.unknown;
  UserModel? _user;
  String? _errorMessage;

  AuthStatus get status => _status;
  UserModel? get user => _user;
  String? get errorMessage => _errorMessage;
  bool get isLoggedIn => _status == AuthStatus.authenticated;

  /// Dipanggil saat app pertama kali dibuka — cek token di storage.
  Future<void> checkAuthStatus() async {
    final loggedIn = await ApiClient.isLoggedIn;
    if (loggedIn) {
      try {
        _user = await _authService.getProfile();
        _status = AuthStatus.authenticated;
      } catch (_) {
        await ApiClient.clearToken();
        _status = AuthStatus.unauthenticated;
      }
    } else {
      _status = AuthStatus.unauthenticated;
    }
    notifyListeners();
  }

  /// Login guru dengan username & password.
  Future<bool> login(String username, String password) async {
    _errorMessage = null;
    try {
      _user = await _authService.login(username, password);
      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _errorMessage = e.message;
      notifyListeners();
      return false;
    } catch (_) {
      _errorMessage = 'Tidak dapat terhubung ke server. Pastikan backend berjalan.';
      notifyListeners();
      return false;
    }
  }

  /// Register akun guru baru.
  Future<bool> register({
    required String namaLengkap,
    required String username,
    required String password,
    required String confirmPassword,
  }) async {
    _errorMessage = null;
    try {
      _user = await _authService.register(
        namaLengkap: namaLengkap,
        username: username,
        password: password,
        confirmPassword: confirmPassword,
      );
      _status = AuthStatus.authenticated;
      notifyListeners();
      return true;
    } on ApiException catch (e) {
      _errorMessage = e.message;
      notifyListeners();
      return false;
    } catch (_) {
      _errorMessage = 'Tidak dapat terhubung ke server. Pastikan backend berjalan.';
      notifyListeners();
      return false;
    }
  }

  /// Logout — hapus token, reset state.
  Future<void> logout() async {
    await _authService.logout();
    _user = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  /// Update data user lokal setelah edit profil berhasil.
  void updateUser(UserModel updated) {
    _user = updated;
    notifyListeners();
  }

  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}
