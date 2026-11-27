import 'package:flutter/material.dart';
import '../../config/app_colors.dart';
import '../../config/app_constants.dart';
import '../../config/app_text_styles.dart';
import '../../data/models/ujian_model.dart';
import '../../data/services/ujian_service.dart';
import 'ujian_form_screen.dart';

class UjianListScreen extends StatefulWidget {
  const UjianListScreen({super.key});

  @override
  State<UjianListScreen> createState() => _UjianListScreenState();
}

class _UjianListScreenState extends State<UjianListScreen> {
  final UjianService _ujianService = UjianService();
  bool _isLoading = true;
  List<UjianModel> _ujianList = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final data = await _ujianService.getUjianList();
      setState(() {
        _ujianList = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _deleteUjian(UjianModel ujian) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Hapus Master Ujian'),
        content: Text('Anda yakin ingin menghapus ${ujian.mataPelajaran} kelas ${ujian.kelas}?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Batal'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: const Text('Hapus', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await _ujianService.deleteUjian(ujian.ujianId);
        _loadData();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Gagal menghapus: $e')));
        }
      }
    }
  }

  Future<void> _openForm([UjianModel? ujian]) async {
    final result = await Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => UjianFormScreen(ujian: ujian)),
    );
    if (result == true) {
      _loadData();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Master Ujian'),
        centerTitle: false,
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _ujianList.isEmpty 
              ? const Center(child: Text('Belum ada master ujian'))
              : ListView.separated(
                  padding: const EdgeInsets.all(AppConstants.paddingLarge),
                  itemCount: _ujianList.length,
                  separatorBuilder: (context, index) => const SizedBox(height: 12),
                  itemBuilder: (context, index) {
                    final ujian = _ujianList[index];
                    return Card(
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        side: const BorderSide(color: AppColors.border),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(ujian.mataPelajaran, style: AppTextStyles.h3),
                                ),
                                Row(
                                  children: [
                                    Text(ujian.tanggalUjian, style: AppTextStyles.bodyTextSmall),
                                    const SizedBox(width: 8),
                                    PopupMenuButton<String>(
                                      onSelected: (val) {
                                        if (val == 'edit') {
                                          _openForm(ujian);
                                        } else if (val == 'delete') {
                                          _deleteUjian(ujian);
                                        }
                                      },
                                      itemBuilder: (BuildContext context) => [
                                        const PopupMenuItem(
                                          value: 'edit',
                                          child: Text('Edit'),
                                        ),
                                        const PopupMenuItem(
                                          value: 'delete',
                                          child: Text('Hapus', style: TextStyle(color: Colors.red)),
                                        ),
                                      ],
                                      child: const Icon(Icons.more_vert, color: AppColors.slate500),
                                    )
                                  ],
                                ),
                              ],
                            ),
                            const Divider(),
                            Text('Kelas: ${ujian.kelas} | Tahun: ${ujian.tahunAjaran}', style: AppTextStyles.bodyText),
                            const SizedBox(height: 8),
                            Text('${ujian.kunciJawaban.length} Soal', style: AppTextStyles.bodyTextSmall.copyWith(color: AppColors.primary)),
                          ],
                        ),
                      ),
                    );
                  },
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: () => _openForm(),
        backgroundColor: AppColors.primary,
        child: const Icon(Icons.add, color: AppColors.white),
      ),
    );
  }
}
