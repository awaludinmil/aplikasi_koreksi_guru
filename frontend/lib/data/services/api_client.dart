import 'dart:io';
import 'package:dio/dio.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../config/app_constants.dart';

const _kTokenKey = 'auth_token';
const _kUserIdKey = 'user_id';

/// Exception kustom agar kode di service tidak perlu diubah.
class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

/// HTTP client terpusat menggunakan Dio.
class ApiClient {
  static final Dio _dio = _createDio();

  static Dio _createDio() {
    final dio = Dio(BaseOptions(
      baseUrl: AppConstants.apiBaseUrl,
      connectTimeout: const Duration(seconds: 60),
      receiveTimeout: const Duration(seconds: 180),
      sendTimeout: const Duration(seconds: 180),
      responseType: ResponseType.json,
    ));

    // Interceptor untuk injeksi token dan logging
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          // Hanya tambahkan token jika bukan request auth yang sengaja di-skip
          if (options.extra['auth'] != false) {
            final token = await getToken();
            if (token != null) {
              options.headers['Authorization'] = 'Bearer $token';
            }
          }
          return handler.next(options);
        },
      ),
    );

    // Logger
    dio.interceptors.add(
      LogInterceptor(
        request: true,
        requestHeader: true,
        requestBody: true,
        responseHeader: false,
        responseBody: true,
        error: true,
      ),
    );

    return dio;
  }

  // ── Token Storage ───────────────────────────────────────────────────

  static Future<String?> getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_kTokenKey);
  }

  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_kTokenKey, token);
  }

  static Future<void> saveUserId(int userId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(_kUserIdKey, userId);
  }

  static Future<int?> getUserId() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_kUserIdKey);
  }

  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_kTokenKey);
    await prefs.remove(_kUserIdKey);
  }

  static Future<bool> get isLoggedIn async {
    final token = await getToken();
    return token != null && token.isNotEmpty;
  }

  // ── Response Parser ──────────────────────────────────────────────────

  static Map<String, dynamic> _parseError(DioException e) {
    if (e.response != null) {
      final data = e.response?.data;
      final msg = (data is Map && data.containsKey('error')) 
          ? data['error'] 
          : (data is Map && data.containsKey('message')) 
              ? data['message'] 
              : 'Terjadi kesalahan pada server';
      throw ApiException(e.response?.statusCode ?? 500, msg.toString());
    } else {
      throw ApiException(500, 'Tidak dapat terhubung ke server');
    }
  }

  // ── HTTP Methods ─────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> get(
    String path, {
    Map<String, dynamic>? query,
    bool auth = true,
  }) async {
    try {
      final res = await _dio.get(
        path, 
        queryParameters: query,
        options: Options(extra: {'auth': auth}),
      );
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      return _parseError(e);
    }
  }

  static Future<Map<String, dynamic>> post(
    String path,
    Map<String, dynamic> body, {
    bool auth = true,
  }) async {
    try {
      final res = await _dio.post(
        path,
        data: body,
        options: Options(extra: {'auth': auth}),
      );
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      return _parseError(e);
    }
  }

  static Future<Map<String, dynamic>> put(
    String path,
    Map<String, dynamic> body, {
    bool auth = true,
  }) async {
    try {
      final res = await _dio.put(
        path,
        data: body,
        options: Options(extra: {'auth': auth}),
      );
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      return _parseError(e);
    }
  }

  static Future<Map<String, dynamic>> delete(
    String path, {
    bool auth = true,
  }) async {
    try {
      final res = await _dio.delete(
        path,
        options: Options(extra: {'auth': auth}),
      );
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      return _parseError(e);
    }
  }

  /// Multipart POST untuk upload file (OCR/Predict) mendukung multiple images
  static Future<Map<String, dynamic>> postMultipartBytes(
    String path, {
    required List<MultipartFile> imageFiles,
    required Map<String, dynamic> fields,
  }) async {
    try {
      final formData = FormData.fromMap({
        ...fields,
        'images': imageFiles,
      });

      final res = await _dio.post(
        path,
        data: formData,
        options: Options(extra: {'auth': true}),
      );
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      return _parseError(e);
    }
  }

  /// Multipart POST untuk upload file (OCR)
  static Future<Map<String, dynamic>> postMultipart(
    String path, {
    required File imageFile,
    required Map<String, String> fields,
  }) async {
    try {
      final formData = FormData.fromMap({
        ...fields,
        'image': await MultipartFile.fromFile(imageFile.path),
      });

      final res = await _dio.post(
        path,
        data: formData,
        options: Options(extra: {'auth': true}),
      );
      return res.data as Map<String, dynamic>;
    } on DioException catch (e) {
      return _parseError(e);
    }
  }
}
