import os

import pytest

from loguru import logger

import warnings

# from unittest.mock import patch, MagicMock, Mock
import tests.testing_medias as test_media
from vikit.video.prompt_based_video import PromptBasedVideo
from vikit.prompt.prompt_factory import PromptFactory
from vikit.video.video import VideoBuildSettings
from vikit.common.context_managers import WorkingFolderContext
from vikit.music_building_context import MusicBuildingContext
import tests.testing_tools as tools  # used to get a library of test prompts
from vikit.prompt.prompt_build_settings import PromptBuildSettings

TEST_PROMPT = "A group of stones in a forest, with symbols"


class TestPromptBasedVideo:

    def setUp(self) -> None:
        warnings.simplefilter("ignore", category=ResourceWarning)
        warnings.simplefilter("ignore", category=UserWarning)
        logger.add("log_test_prompt_based_video.txt", rotation="10 MB")

    @pytest.mark.unit
    def test_no_prompt_text(self):
        with pytest.raises(ValueError):
            _ = PromptBasedVideo(str(""))

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_title(self):
        with WorkingFolderContext():
            build_settings = VideoBuildSettings()
            prompt = await PromptFactory(
                ml_gateway=build_settings.get_ml_models_gateway(),
            ).create_prompt_from_text(
                "A group of stones",
            )

            video_title = PromptBasedVideo(prompt=prompt).get_title()
            assert len(video_title) > 0  # we should have a file of at least 1 character

    @pytest.mark.local_integration
    @pytest.mark.asyncio
    async def test_build_single_video_no_bg_music_without_subs(self):
        with WorkingFolderContext():
            pbvid = PromptBasedVideo(
                await PromptFactory().create_prompt_from_text(
                    prompt_text=TEST_PROMPT,
                )
            )
            await pbvid.build()

            assert pbvid.media_url, "media URL is None, was not updated"
            assert pbvid._background_music_file_name is None
            assert os.path.exists(pbvid.media_url), "The generated video does not exist"

    @pytest.mark.local_integration
    @pytest.mark.asyncio
    async def test_build_single_video_no_bg_music_with_subtitles(self):
        with WorkingFolderContext():
            pbvid = PromptBasedVideo(tools.test_prompt_library["moss_stones-train_boy"])
            await pbvid.build(
                build_settings=VideoBuildSettings(include_read_aloud_prompt=True)
            )

            assert pbvid._background_music_file_name is None
            assert pbvid.media_url, "media URL was not updated"
            assert os.path.exists(pbvid.media_url), "The generated video does not exist"

    @pytest.mark.local_integration
    @pytest.mark.asyncio
    async def test_build_single_video_with_default_bg_music_with_subtitles(self):
        with WorkingFolderContext():
            pbvid = PromptBasedVideo(tools.test_prompt_library["moss_stones-train_boy"])
            await pbvid.build(
                build_settings=VideoBuildSettings(
                    include_read_aloud_prompt=True,
                    music_building_context=MusicBuildingContext(
                        apply_background_music=True, generate_background_music=False
                    ),
                )
            )

            assert pbvid.media_url, "media URL was not updated"
            assert os.path.exists(pbvid.media_url), "The generated video does not exist"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_build_tom_cruse_video(self):
        with WorkingFolderContext():

            bld_settings = VideoBuildSettings(
                include_read_aloud_prompt=True,
                music_building_context=MusicBuildingContext(
                    apply_background_music=True,
                    generate_background_music=True,
                ),
                test_mode=False,
            )

            prompt = await PromptFactory(
                ml_gateway=bld_settings.get_ml_models_gateway()
            ).create_prompt_from_text(
                """Tom Cruise's face reflects focus, his eyes filled with purpose and drive. He drives a moto very fast on a 
                skyscrapper rooftop, jumps from the moto to an 
                helicopter, this last 3 seconds, then Tom Cruse dives into a swimming pool from the helicopter while the helicopter without pilot crashes 
                  near the beach"""
            )
            pbvid = PromptBasedVideo(prompt=prompt)

            pbvid = await pbvid.build(
                build_settings=bld_settings,
            )
            assert pbvid.media_url, "media URL was not updated"
            assert os.path.exists(pbvid.media_url), "The generated video does not exist"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_build_single_video_with_generated_bg_music_with_subtitles(self):
        with WorkingFolderContext():

            bld_settings = VideoBuildSettings(
                include_read_aloud_prompt=True,
                music_building_context=MusicBuildingContext(
                    apply_background_music=True,
                    generate_background_music=True,
                ),
                test_mode=False,
            )

            prompt = await PromptFactory(
                ml_gateway=bld_settings.get_ml_models_gateway()
            ).create_prompt_from_text(TEST_PROMPT)
            pbvid = PromptBasedVideo(prompt=prompt)

            pbvid = await pbvid.build(
                build_settings=bld_settings,
            )
            assert pbvid.media_url, "media URL was not updated"
            assert os.path.exists(pbvid.media_url), "The generated video does not exist"

    @pytest.mark.local_integration
    @pytest.mark.asyncio
    async def test_generate_short_video_single_sub(self):
        with WorkingFolderContext():

            prompt = await PromptFactory().create_prompt_from_text(
                "A group of stones in a forest",
            )
            pbv = PromptBasedVideo(prompt=prompt)
            result = await pbv.build()
            assert result is not None
            assert os.path.exists(result.media_url)

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skip
    async def test_use_recorded_prompt_infer_lyrics_sof(self):
        """
        Experimental: see how giving a music track would work as a prompt
            Letting the model infer the lyrics of the song
            Letting the model imagine a scenario vor the video with movie director's instructions
            use the audio track as a prompt

            ...please use your own music track for obvious copyright reasons :)
        """
        with WorkingFolderContext():
            bld_settings = VideoBuildSettings(
                include_read_aloud_prompt=True,
                musicBuildingContext=MusicBuildingContext(
                    generate_background_music=False,
                    apply_background_music=True,
                    use_recorded_prompt_as_audio=True,
                ),
                test_mode=False,
            )

            test_prompt = await PromptFactory(
                bld_settings.get_ml_models_gateway()
            ).create_prompt_from_text(
                test_media.sof,
            )
            bld_settings.prompt = test_prompt

            video = PromptBasedVideo(test_prompt)
            vid_final = await video.build(build_settings=bld_settings)

            assert vid_final.media_url is not None
            assert vid_final.background_music is not None

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_build_nominal_prompt_without_bk_music_wthout_subs(self):
        with WorkingFolderContext():
            build_settings = VideoBuildSettings(
                music_building_context=MusicBuildingContext(
                    apply_background_music=False
                ),
                include_read_aloud_prompt=False,
                test_mode=False,
            )
            test_prompt = tools.test_prompt_library["moss_stones-train_boy"]
            video = PromptBasedVideo(test_prompt)
            await video.build(build_settings=build_settings)

            assert video.media_url is not None
            assert os.path.exists(video.media_url)

    # @pytest.mark.skip("To be activated on case by case basis")
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_reunion_island_prompt_with_bk_music_subs(self):
        with WorkingFolderContext():
            bld_sett = VideoBuildSettings(
                music_building_context=MusicBuildingContext(
                    apply_background_music=True
                ),
                include_read_aloud_prompt=True,
                test_mode=False,
            )
            test_prompt = await PromptFactory(
                bld_sett.get_ml_models_gateway()
            ).create_prompt_from_text(
                """A travel over Reunion Island, taken fomm birdview at 2000meters above 
                the ocean, flying over the volcano, the forest, the coast and the city of Saint Denis
                , then flying just over the roads in curvy mountain areas, and finally landing on the beach""",
            )

            video = PromptBasedVideo(prompt=test_prompt)
            await video.build(bld_sett)

            assert video.media_url is not None
            assert os.path.exists(video.media_url)

    @pytest.mark.integration
    @pytest.mark.asyncio
    @pytest.mark.skip
    async def test_reunion_island_prompt_with_generated_bk_music_subs(self):
        with WorkingFolderContext():
            bld_sett = VideoBuildSettings(
                music_building_context=MusicBuildingContext(
                    apply_background_music=True,
                    generate_background_music=True,
                ),
                include_read_aloud_prompt=True,
                test_mode=False,
            )
            test_prompt = await PromptFactory(
                bld_sett.get_ml_models_gateway()
            ).create_prompt_from_text(
                """A travel over Reunion Island, taken fomm birdview at 2000meters above 
                the ocean, flying over the volcano, the forest, the coast and the city of Saint Denis
                , then flying just over the roads in curvy mountain areas, and finally landing on the beach""",
            )

            video = PromptBasedVideo(prompt=test_prompt)
            await video.build(bld_sett)

            assert video.media_url is not None
            assert os.path.exists(video.media_url)

    @pytest.mark.local_integration
    @pytest.mark.skip
    @pytest.mark.asyncio
    async def test_local_int_reunion_island_prompt_with_bk_music_subs(self):
        with WorkingFolderContext():
            bld_sett = VideoBuildSettings(
                music_building_context=MusicBuildingContext(
                    apply_background_music=True
                ),
                include_read_aloud_prompt=True,
                test_mode=False,
            )
            test_prompt = await PromptFactory(
                bld_sett.get_ml_models_gateway()
            ).create_prompt_from_text(
                """A travel over Reunion Island, taken fomm birdview at 2000meters above 
                the ocean, flying over the volcano, the forest, the coast and the city of Saint Denis
                , then flying just over the roads in curvy mountain areas, and finally landing on the beach""",
            )

            video = PromptBasedVideo(prompt=test_prompt)
            await video.build(bld_sett)

            assert video.media_url is not None
            assert os.path.exists(video.media_url)

    @pytest.mark.local_integration
    @pytest.mark.asyncio
    @pytest.mark.skip
    async def test_collab_integration(self):
        with WorkingFolderContext():
            prompt = await PromptFactory(
                prompt_build_settings=PromptBuildSettings(test_mode=True)
            ).create_prompt_from_text(
                "A young girl traveling in the train alongside Mediterranean coast",
            )
            video_build_settings = VideoBuildSettings(
                music_building_context=MusicBuildingContext(
                    apply_background_music=True, generate_background_music=True
                ),
                test_mode=True,
                include_read_aloud_prompt=True,
                prompt=prompt,
            )
            video = PromptBasedVideo(prompt=prompt)

            await video.build(build_settings=video_build_settings)

            assert video.media_url is not None
            assert os.path.exists(video.media_url)
